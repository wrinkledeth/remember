from unittest.mock import patch

from remember.anki_client import AnkiNote
from remember.parser import InsightCard
from remember.sync import sync, SyncResult


# --- helpers ---

CARD_A = InsightCard(id="001", front="Front A", back="Back A")
CARD_B = InsightCard(id="002", front="Front B", back="Back B")
CARD_C = InsightCard(id="003", front="Front C", back="Back C")

ANKI_NOTE_B = AnkiNote(note_id=100, card_id="002", front="Front B", back="Back B")
ANKI_NOTE_B_CHANGED = AnkiNote(note_id=100, card_id="002", front="Old front", back="Old back")
ANKI_NOTE_ORPHAN = AnkiNote(note_id=200, card_id="099", front="Orphan", back="Orphan back")


def _run_sync(cards, existing_notes=None, **kwargs):
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
    ):
        result = sync("fake.md", **kwargs)
        mocks = {
            "ensure_deck": mock_ensure,
            "add_note": mock_add,
            "update_note_fields": mock_update_fields,
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

def test_orphaned_cards():
    result, mocks = _run_sync([CARD_A], existing_notes=[ANKI_NOTE_ORPHAN])
    assert result.orphaned == 1
    assert result.created == 1


# --- dry run ---

def test_dry_run_no_writes():
    result, mocks = _run_sync([CARD_A, CARD_B], dry_run=True)
    assert result.created == 2
    mocks["add_note"].assert_not_called()
    mocks["update_note_fields"].assert_not_called()


def test_dry_run_with_changes():
    result, mocks = _run_sync([CARD_B], existing_notes=[ANKI_NOTE_B_CHANGED], dry_run=True)
    assert result.updated == 1
    mocks["update_note_fields"].assert_not_called()


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
        patch("remember.sync.update_note_fields", side_effect=RuntimeError("network error")),
    ):
        result = sync("fake.md")

    assert len(result.errors) == 1
    assert "002" in result.errors[0]


# --- empty file ---

def test_no_cards_returns_empty_result():
    result, mocks = _run_sync([])
    assert result == SyncResult()
    mocks["ensure_deck"].assert_not_called()
