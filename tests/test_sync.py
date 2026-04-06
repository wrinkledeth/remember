import os
import tempfile
import textwrap
from unittest.mock import patch

from remember.anki_client import AnkiNote
from remember.parser import InsightCard
from remember.sync import sync, SyncResult


# --- helpers ---

CARD_A = InsightCard(id="001", front="Front A", back="Back A")
CARD_B = InsightCard(id="002", front="Front B", back="Back B")
CARD_C = InsightCard(id="003", front="Front C", back="Back C")

ANKI_NOTE_B = AnkiNote(note_id=100, card_id="002", front="Front B", back="Back B", mod=1000)
ANKI_NOTE_B_CHANGED = AnkiNote(
    note_id=100, card_id="002", front="Old front", back="Old back", mod=1000
)
ANKI_NOTE_B_CHANGED_NEWER = AnkiNote(
    note_id=100, card_id="002", front="Old front", back="Old back", mod=9999999999
)
ANKI_NOTE_ORPHAN = AnkiNote(
    note_id=200, card_id="099", front="Orphan", back="Orphan back", mod=1000
)


def _run_sync(cards, existing_notes=None, input_response="n", file_mtime=5000, verbose=False):
    """Run sync with mocked dependencies, return (result, mocks)."""
    existing = existing_notes or []
    note_ids = [n.note_id for n in existing]

    with (
        patch("remember.sync.parse_insights", return_value=cards),
        patch("remember.sync.ensure_deck") as mock_ensure,
        patch("remember.sync.find_synced_notes", return_value=note_ids),
        patch("remember.sync.get_notes_info", return_value=existing),
        patch("remember.sync.add_note", return_value=1) as mock_add,
        patch("remember.sync.update_note_fields") as mock_update_fields,
        patch("remember.sync.delete_notes") as mock_delete,
        patch("remember.sync._write_anki_to_markdown") as mock_write_anki,
        patch("os.path.getmtime", return_value=file_mtime),
        patch("builtins.input", return_value=input_response),
    ):
        result = sync("fake.md", verbose=verbose)
        mocks = {
            "ensure_deck": mock_ensure,
            "add_note": mock_add,
            "update_note_fields": mock_update_fields,
            "delete_notes": mock_delete,
            "write_anki_to_markdown": mock_write_anki,
        }
        return result, mocks


# --- all new cards ---


def test_all_new_cards():
    result, mocks = _run_sync([CARD_A, CARD_B])
    assert result.created == 2
    assert result.updated == 0
    assert result.unchanged == 0
    assert mocks["add_note"].call_count == 2


def test_new_card_calls_add_note_with_correct_args():
    result, mocks = _run_sync([CARD_A])
    mocks["add_note"].assert_called_once_with(
        "Life Insights", "Front A", "Back A", "001"
    )


# --- mix of new, changed, unchanged ---


def test_mixed_scenario():
    result, mocks = _run_sync([CARD_A, CARD_B], existing_notes=[ANKI_NOTE_B])
    assert result.created == 1
    assert result.unchanged == 1
    assert result.updated == 0


def test_changed_fields_triggers_update():
    result, mocks = _run_sync([CARD_B], existing_notes=[ANKI_NOTE_B_CHANGED])
    assert result.updated == 1
    assert result.created == 0
    mocks["update_note_fields"].assert_called_once_with(100, "Front B", "Back B")


# --- orphaned cards ---


def test_orphaned_cards_decline_delete():
    result, mocks = _run_sync([CARD_A], existing_notes=[ANKI_NOTE_ORPHAN], input_response="n")
    assert result.orphaned == 1
    assert result.deleted == 0
    assert result.created == 1
    mocks["delete_notes"].assert_not_called()


def test_orphaned_cards_accept_delete():
    result, mocks = _run_sync([CARD_A], existing_notes=[ANKI_NOTE_ORPHAN], input_response="y")
    assert result.orphaned == 1
    assert result.deleted == 1
    assert result.created == 1
    mocks["delete_notes"].assert_called_once_with([200])


# --- conflict resolution ---


def test_conflict_markdown_newer_auto_pushes():
    """When markdown is newer, update Anki without prompting."""
    result, mocks = _run_sync(
        [CARD_B], existing_notes=[ANKI_NOTE_B_CHANGED], file_mtime=5000
    )
    # ANKI_NOTE_B_CHANGED has mod=1000, file_mtime=5000 → markdown is newer
    assert result.updated == 1
    mocks["update_note_fields"].assert_called_once()


def test_conflict_anki_newer_keep_markdown():
    """When Anki is newer and user picks markdown, push to Anki."""
    result, mocks = _run_sync(
        [CARD_B], existing_notes=[ANKI_NOTE_B_CHANGED_NEWER], input_response="m"
    )
    assert result.updated == 1
    mocks["update_note_fields"].assert_called_once_with(100, "Front B", "Back B")
    mocks["write_anki_to_markdown"].assert_not_called()


def test_conflict_anki_newer_keep_anki():
    """When Anki is newer and user picks Anki, pull to markdown."""
    result, mocks = _run_sync(
        [CARD_B], existing_notes=[ANKI_NOTE_B_CHANGED_NEWER], input_response="a"
    )
    assert result.pulled == 1
    assert result.updated == 0
    mocks["write_anki_to_markdown"].assert_called_once_with(
        "fake.md", "002", "Old front", "Old back"
    )
    mocks["update_note_fields"].assert_not_called()


def test_conflict_anki_newer_skip():
    """When Anki is newer and user skips, do nothing."""
    result, mocks = _run_sync(
        [CARD_B], existing_notes=[ANKI_NOTE_B_CHANGED_NEWER], input_response="s"
    )
    assert result.unchanged == 1
    assert result.updated == 0
    assert result.pulled == 0
    mocks["update_note_fields"].assert_not_called()
    mocks["write_anki_to_markdown"].assert_not_called()


# --- error handling ---


def test_add_note_error_collected():
    """One card fails, the other still syncs."""
    with (
        patch("remember.sync.parse_insights", return_value=[CARD_A, CARD_B]),
        patch("remember.sync.ensure_deck"),
        patch("remember.sync.find_synced_notes", return_value=[]),
        patch("remember.sync.get_notes_info", return_value=[]),
        patch("remember.sync.add_note", side_effect=[RuntimeError("duplicate"), 1]),
        patch("remember.sync.update_note_fields"),
        patch("remember.sync.delete_notes"),
        patch("os.path.getmtime", return_value=5000),
        patch("builtins.input", return_value="n"),
    ):
        result = sync("fake.md")

    assert len(result.errors) == 1
    assert "001" in result.errors[0]
    assert "duplicate" in result.errors[0]
    assert result.created == 1


def test_update_error_collected():
    """Update failure is collected, doesn't crash."""
    with (
        patch("remember.sync.parse_insights", return_value=[CARD_B]),
        patch("remember.sync.ensure_deck"),
        patch("remember.sync.find_synced_notes", return_value=[100]),
        patch("remember.sync.get_notes_info", return_value=[ANKI_NOTE_B_CHANGED]),
        patch("remember.sync.add_note"),
        patch(
            "remember.sync.update_note_fields",
            side_effect=RuntimeError("network error"),
        ),
        patch("remember.sync.delete_notes"),
        patch("os.path.getmtime", return_value=5000),
        patch("builtins.input", return_value="n"),
    ):
        result = sync("fake.md")

    assert len(result.errors) == 1
    assert "002" in result.errors[0]


# --- empty file ---


def test_no_cards_returns_empty_result():
    result, mocks = _run_sync([])
    assert result == SyncResult()
    mocks["ensure_deck"].assert_not_called()


# --- stamping ---


def _write_temp_md(content: str) -> str:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


def test_stamp_inserts_id_into_file():
    md = textwrap.dedent("""\
        # Life Insights

        ## A new card without an ID
        ---
        This is the back.
    """)
    path = _write_temp_md(md)
    try:
        with (
            patch("remember.sync.ensure_deck"),
            patch("remember.sync.find_synced_notes", return_value=[]),
            patch("remember.sync.get_notes_info", return_value=[]),
            patch("remember.sync.add_note", return_value=1),
            patch("remember.sync.uuid.uuid4") as mock_uuid,
        ):
            mock_uuid.return_value.hex = "abcdef1234567890"
            result = sync(path)

        assert result.stamped == 1
        assert result.created == 1

        with open(path, encoding="utf-8") as f:
            updated = f.read()
        assert "<!-- id: abcdef12 -->" in updated
        # ID should appear right before ---
        lines = updated.split("\n")
        id_idx = next(i for i, l in enumerate(lines) if "<!-- id: abcdef12 -->" in l)
        sep_idx = next(i for i, l in enumerate(lines) if l.strip() == "---" and i > id_idx)
        assert sep_idx == id_idx + 1
    finally:
        os.unlink(path)


def test_stamp_mixed_cards():
    md = textwrap.dedent("""\
        # Life Insights

        ## Existing card
        <!-- id: 001 -->
        ---
        Already has an ID.

        ## New card
        ---
        No ID here.
    """)
    path = _write_temp_md(md)
    try:
        with (
            patch("remember.sync.ensure_deck"),
            patch("remember.sync.find_synced_notes", return_value=[]),
            patch("remember.sync.get_notes_info", return_value=[]),
            patch("remember.sync.add_note", return_value=1),
        ):
            result = sync(path)

        assert result.stamped == 1
        assert result.created == 2

        with open(path, encoding="utf-8") as f:
            updated = f.read()
        # Original ID preserved
        assert "<!-- id: 001 -->" in updated
        # New ID added (some random hex)
        lines = updated.split("\n")
        new_card_idx = next(i for i, l in enumerate(lines) if "## New card" in l)
        assert lines[new_card_idx + 1].startswith("<!-- id:")
    finally:
        os.unlink(path)
