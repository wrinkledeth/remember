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


def _run_pull(notes, deck="Test Deck", verbose=False):
    """Run pull with mocked AnkiConnect, return (result, output_path, tmpdir)."""
    tmpdir = tempfile.mkdtemp()
    cards_dir = Path(tmpdir)
    note_ids = [n.note_id for n in notes]

    with (
        patch("remember.pull.find_notes_in_deck", return_value=note_ids) as mock_find,
        patch("remember.pull.get_notes_info", return_value=notes) as mock_info,
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


def test_skip_non_basic():
    result, _, _ = _run_pull([BASIC_NOTE_A, NON_BASIC_NOTE])
    assert result.pulled == 1
    assert result.skipped_non_basic == 1


def test_skip_media_img():
    result, _, _ = _run_pull([BASIC_NOTE_A, MEDIA_NOTE])
    assert result.pulled == 1
    assert result.skipped_media == 1


def test_skip_media_sound():
    result, _, _ = _run_pull([BASIC_NOTE_A, SOUND_NOTE])
    assert result.pulled == 1
    assert result.skipped_media == 1


def test_skip_already_tracked():
    result, _, _ = _run_pull([BASIC_NOTE_A, TRACKED_NOTE])
    assert result.pulled == 1
    assert result.already_tracked == 1


def test_all_filtered_no_file_created():
    result, cards_dir, _ = _run_pull([NON_BASIC_NOTE, MEDIA_NOTE, TRACKED_NOTE])
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
    with patch("remember.pull.find_notes_in_deck", return_value=[]):
        result = pull(deck="Empty", cards_dir=Path(tmpdir))
    assert result.pulled == 0


# --- verbose output ---


def test_verbose_shows_actions(capsys):
    _run_pull([BASIC_NOTE_A, NON_BASIC_NOTE, TRACKED_NOTE], verbose=True)
    captured = capsys.readouterr()
    assert "[pull]" in captured.out
    assert "[skip] non-Basic" in captured.out
    assert "[skip] already tracked" in captured.out
