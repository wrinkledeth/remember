import textwrap
from pathlib import Path
from unittest.mock import patch

from remember.anki_client import AnkiNote
from remember.status import status


def _write_md(tmp_path: Path, name: str, content: str) -> Path:
    f = tmp_path / name
    f.write_text(textwrap.dedent(content))
    return f


def test_status_all_synced(tmp_path, capsys):
    md = _write_md(tmp_path, "vocab.md", """\
        # Vocab

        ## What is HTTP?
        <!-- id: 001 -->
        ---
        HyperText Transfer Protocol.
    """)

    anki_note = AnkiNote(note_id=100, card_id="001", front="What is HTTP?", back="HyperText Transfer Protocol.")

    with (
        patch("remember.status.find_synced_notes", return_value=[100]),
        patch("remember.status.get_notes_info", return_value=[anki_note]),
    ):
        status([md], tmp_path)

    output = capsys.readouterr().out
    assert "1 synced" in output


def test_status_new_card(tmp_path, capsys):
    md = _write_md(tmp_path, "vocab.md", """\
        # Vocab

        ## What is HTTP?
        <!-- id: 001 -->
        ---
        HyperText Transfer Protocol.
    """)

    with (
        patch("remember.status.find_synced_notes", return_value=[]),
        patch("remember.status.get_notes_info", return_value=[]),
    ):
        status([md], tmp_path)

    output = capsys.readouterr().out
    assert "1 new" in output


def test_status_changed_card(tmp_path, capsys):
    md = _write_md(tmp_path, "vocab.md", """\
        # Vocab

        ## What is HTTP?
        <!-- id: 001 -->
        ---
        Updated answer.
    """)

    anki_note = AnkiNote(note_id=100, card_id="001", front="What is HTTP?", back="Old answer.")

    with (
        patch("remember.status.find_synced_notes", return_value=[100]),
        patch("remember.status.get_notes_info", return_value=[anki_note]),
    ):
        status([md], tmp_path)

    output = capsys.readouterr().out
    assert "1 changed" in output


def test_status_orphaned_card(tmp_path, capsys):
    md = _write_md(tmp_path, "vocab.md", """\
        # Vocab

        ## What is HTTP?
        <!-- id: 001 -->
        ---
        Answer.
    """)

    anki_synced = AnkiNote(note_id=100, card_id="001", front="What is HTTP?", back="Answer.")
    anki_orphan = AnkiNote(note_id=200, card_id="099", front="Deleted card", back="Gone.")

    with (
        patch("remember.status.find_synced_notes", return_value=[100, 200]),
        patch("remember.status.get_notes_info", return_value=[anki_synced, anki_orphan]),
    ):
        status([md], tmp_path)

    output = capsys.readouterr().out
    assert "1 orphaned" in output


def test_status_unstamped_card(tmp_path, capsys):
    md = _write_md(tmp_path, "vocab.md", """\
        # Vocab

        ## A card with no ID
        ---
        Back text.
    """)

    with (
        patch("remember.status.find_synced_notes", return_value=[]),
        patch("remember.status.get_notes_info", return_value=[]),
    ):
        status([md], tmp_path)

    output = capsys.readouterr().out
    assert "1 unstamped" in output


def test_status_multiple_files_shows_total(tmp_path, capsys):
    md1 = _write_md(tmp_path, "a.md", """\
        # A

        ## Card one
        <!-- id: 001 -->
        ---
        Back one.
    """)
    md2 = _write_md(tmp_path, "b.md", """\
        # B

        ## Card two
        <!-- id: 002 -->
        ---
        Back two.
    """)

    with (
        patch("remember.status.find_synced_notes", return_value=[]),
        patch("remember.status.get_notes_info", return_value=[]),
    ):
        status([md1, md2], tmp_path)

    output = capsys.readouterr().out
    assert "Total" in output
    assert "2 cards" in output
