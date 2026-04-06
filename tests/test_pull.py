import os
import tempfile
from pathlib import Path
from unittest.mock import patch, call

from remember.anki_client import AnkiNote
from remember.pull import pull, file_path_from_deck, PullResult


# --- fixtures ---

BASIC_NOTE_A = AnkiNote(
    note_id=1, card_id="", front="What is HTTP?", back="HyperText Transfer Protocol",
    model_name="Basic",
)
BASIC_NOTE_B = AnkiNote(
    note_id=2, card_id="", front="What is DNS?", back="Domain Name System",
    model_name="Basic",
)
NON_BASIC_NOTE = AnkiNote(
    note_id=3, card_id="", front="Cloze {{c1::test}}", back="",
    model_name="Cloze",
)
NON_BASIC_WITH_FIELDS = AnkiNote(
    note_id=7, card_id="", front="Custom front", back="Custom back",
    model_name="Custom Model",
)
MEDIA_NOTE = AnkiNote(
    note_id=4, card_id="", front="Image card", back='<img src="pic.jpg">',
    model_name="Basic",
)
SOUND_NOTE = AnkiNote(
    note_id=5, card_id="", front="Sound card", back="[sound:audio.mp3]",
    model_name="Basic",
)
TRACKED_NOTE = AnkiNote(
    note_id=6, card_id="abc12345", front="Already tracked", back="Has ID tag",
    model_name="Basic",
)


def _run_pull(notes, deck="Test Deck", deck_names=None, verbose=False):
    """Run pull with mocked AnkiConnect, return (result, cards_dir, mock_tags)."""
    tmpdir = tempfile.mkdtemp()
    cards_dir = Path(tmpdir)
    note_ids = [n.note_id for n in notes]
    if deck_names is None:
        deck_names = [deck]

    with (
        patch("remember.pull.get_deck_names", return_value=deck_names),
        patch("remember.pull.find_notes_in_deck", return_value=note_ids),
        patch("remember.pull.get_notes_info", return_value=notes),
        patch("remember.pull.add_tags") as mock_tags,
    ):
        result = pull(deck=deck, cards_dir=cards_dir, verbose=verbose)
        return result, cards_dir, mock_tags


# --- basic pull ---


def test_pull_basic_cards():
    result, cards_dir, mock_tags = _run_pull([BASIC_NOTE_A, BASIC_NOTE_B])
    assert result.pulled == 2
    output = cards_dir / "test-deck.md"
    assert output.exists()
    content = output.read_text()
    assert "# Test Deck" in content
    assert "## What is HTTP?" in content
    assert "HyperText Transfer Protocol" in content
    assert "## What is DNS?" in content
    assert "Domain Name System" in content
    assert content.count("<!-- id:") == 2
    assert content.count("---") == 2
    assert mock_tags.call_count == 2


def test_pull_generates_unique_ids():
    result, cards_dir, mock_tags = _run_pull([BASIC_NOTE_A, BASIC_NOTE_B])
    output = cards_dir / "test-deck.md"
    content = output.read_text()
    import re
    ids = re.findall(r"<!-- id: (\w+) -->", content)
    assert len(ids) == 2
    assert ids[0] != ids[1]


# --- filtering ---


def test_skip_non_basic_without_fields():
    result, _, _ = _run_pull([BASIC_NOTE_A, NON_BASIC_NOTE])
    assert result.pulled == 1
    assert result.skipped_non_basic == 1


def test_pull_non_basic_with_front_and_back():
    result, cards_dir, _ = _run_pull([NON_BASIC_WITH_FIELDS])
    assert result.pulled == 1
    assert result.skipped_non_basic == 0


def test_skip_media_img():
    result, _, _ = _run_pull([BASIC_NOTE_A, MEDIA_NOTE])
    assert result.pulled == 1
    assert result.skipped_media == 1


def test_skip_media_sound():
    result, _, _ = _run_pull([BASIC_NOTE_A, SOUND_NOTE])
    assert result.pulled == 1
    assert result.skipped_media == 1


def test_skip_already_tracked_when_file_exists():
    """Tagged card with matching local file is skipped."""
    tmpdir = tempfile.mkdtemp()
    cards_dir = Path(tmpdir)
    # Create a file that contains the tracked ID
    md = cards_dir / "test-deck.md"
    md.write_text("## Already tracked\n<!-- id: abc12345 -->\n---\nHas ID tag\n\n")

    with (
        patch("remember.pull.get_deck_names", return_value=["Test Deck"]),
        patch("remember.pull.find_notes_in_deck", return_value=[1, 6]),
        patch("remember.pull.get_notes_info", return_value=[BASIC_NOTE_A, TRACKED_NOTE]),
        patch("remember.pull.add_tags") as mock_tags,
    ):
        result = pull(deck="Test Deck", cards_dir=cards_dir)

    assert result.pulled == 1
    assert result.already_tracked == 1


def test_repull_tagged_card_when_file_deleted():
    """Tagged card whose ID is NOT in any local file gets re-pulled."""
    tmpdir = tempfile.mkdtemp()
    cards_dir = Path(tmpdir)
    # No local files — the file was deleted

    with (
        patch("remember.pull.get_deck_names", return_value=["Test Deck"]),
        patch("remember.pull.find_notes_in_deck", return_value=[6]),
        patch("remember.pull.get_notes_info", return_value=[TRACKED_NOTE]),
        patch("remember.pull.add_tags") as mock_tags,
    ):
        result = pull(deck="Test Deck", cards_dir=cards_dir)

    assert result.pulled == 1
    assert result.already_tracked == 0
    # Should reuse existing card_id, not generate a new one
    output = cards_dir / "test-deck.md"
    content = output.read_text()
    assert "<!-- id: abc12345 -->" in content
    # Should NOT re-tag since card already has the tag
    mock_tags.assert_not_called()


def test_all_filtered_no_file_created():
    """Cards that are all filtered out produce no file."""
    tmpdir = tempfile.mkdtemp()
    cards_dir = Path(tmpdir)
    # Create file with the tracked ID so it's truly skipped
    md = cards_dir / "existing.md"
    md.write_text("<!-- id: abc12345 -->\n")

    with (
        patch("remember.pull.get_deck_names", return_value=["Test Deck"]),
        patch("remember.pull.find_notes_in_deck", return_value=[3, 4, 6]),
        patch("remember.pull.get_notes_info", return_value=[NON_BASIC_NOTE, MEDIA_NOTE, TRACKED_NOTE]),
        patch("remember.pull.add_tags"),
    ):
        result = pull(deck="Test Deck", cards_dir=cards_dir)

    assert result.pulled == 0
    output = cards_dir / "test-deck.md"
    assert not output.exists()


# --- append to existing ---


def test_append_to_existing_file():
    tmpdir = tempfile.mkdtemp()
    cards_dir = Path(tmpdir)
    output = cards_dir / "test-deck.md"
    output.write_text("# Test Deck\n\n## Existing card\n<!-- id: existing1 -->\n---\nExisting back\n\n")

    with (
        patch("remember.pull.get_deck_names", return_value=["Test Deck"]),
        patch("remember.pull.find_notes_in_deck", return_value=[1]),
        patch("remember.pull.get_notes_info", return_value=[BASIC_NOTE_A]),
        patch("remember.pull.add_tags"),
    ):
        result = pull(deck="Test Deck", cards_dir=cards_dir)

    assert result.pulled == 1
    content = output.read_text()
    assert "## Existing card" in content
    assert "## What is HTTP?" in content
    assert content.index("## Existing card") < content.index("## What is HTTP?")


# --- subdeck recursion ---


def test_pull_recurses_into_subdecks():
    tmpdir = tempfile.mkdtemp()
    cards_dir = Path(tmpdir)
    all_decks = ["Tech", "Tech::Python", "Tech::Web", "Other"]

    def fake_find(deck, exact=False):
        if deck == "Tech::Python":
            return [1]
        if deck == "Tech::Web":
            return [2]
        if deck == "Tech":
            return []
        return []

    def fake_info(note_ids):
        if note_ids == [1]:
            return [BASIC_NOTE_A]
        if note_ids == [2]:
            return [BASIC_NOTE_B]
        return []

    with (
        patch("remember.pull.get_deck_names", return_value=all_decks),
        patch("remember.pull.find_notes_in_deck", side_effect=fake_find),
        patch("remember.pull.get_notes_info", side_effect=fake_info),
        patch("remember.pull.add_tags"),
    ):
        result = pull(deck="Tech", cards_dir=cards_dir)

    assert result.pulled == 2
    assert (cards_dir / "tech" / "python.md").exists()
    assert (cards_dir / "tech" / "web.md").exists()
    assert "What is HTTP?" in (cards_dir / "tech" / "python.md").read_text()
    assert "What is DNS?" in (cards_dir / "tech" / "web.md").read_text()


def test_pull_no_matching_deck():
    tmpdir = tempfile.mkdtemp()
    with patch("remember.pull.get_deck_names", return_value=["Other"]):
        result = pull(deck="Nonexistent", cards_dir=Path(tmpdir))
    assert result.pulled == 0


# --- deck name to file path ---


def test_file_path_simple():
    assert file_path_from_deck("Cooking", Path("/cards")) == Path("/cards/cooking.md")


def test_file_path_nested():
    assert file_path_from_deck("Spanish::Vocab", Path("/cards")) == Path("/cards/spanish/vocab.md")


def test_file_path_deep_nested():
    assert file_path_from_deck("Languages::Spanish::Verbs", Path("/cards")) == Path("/cards/languages/spanish/verbs.md")


def test_file_path_spaces():
    assert file_path_from_deck("Life Insights", Path("/cards")) == Path("/cards/life-insights.md")


# --- empty deck ---


def test_empty_deck():
    tmpdir = tempfile.mkdtemp()
    with (
        patch("remember.pull.get_deck_names", return_value=["Empty"]),
        patch("remember.pull.find_notes_in_deck", return_value=[]),
    ):
        result = pull(deck="Empty", cards_dir=Path(tmpdir))
    assert result.pulled == 0


# --- verbose output ---


def test_verbose_shows_actions(capsys):
    """Verbose mode shows skip reasons for filtered cards."""
    tmpdir = tempfile.mkdtemp()
    cards_dir = Path(tmpdir)
    # Create file with tracked ID so it's skipped
    md = cards_dir / "test-deck.md"
    md.write_text("<!-- id: abc12345 -->\n")

    with (
        patch("remember.pull.get_deck_names", return_value=["Test Deck"]),
        patch("remember.pull.find_notes_in_deck", return_value=[1, 3, 6]),
        patch("remember.pull.get_notes_info", return_value=[BASIC_NOTE_A, NON_BASIC_NOTE, TRACKED_NOTE]),
        patch("remember.pull.add_tags"),
    ):
        pull(deck="Test Deck", cards_dir=cards_dir, verbose=True)

    captured = capsys.readouterr()
    assert "[pull]" in captured.out
    assert "[skip] non-Basic" in captured.out
    assert "[skip] already tracked" in captured.out
