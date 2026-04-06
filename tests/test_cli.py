from pathlib import Path

from remember.cli import _deck_name_from_path, _collect_files


def test_deck_name_single_file():
    root = Path("/cards")
    assert _deck_name_from_path(Path("/cards/vocab.md"), root) == "Vocab"


def test_deck_name_nested():
    root = Path("/cards")
    assert _deck_name_from_path(Path("/cards/spanish/vocab.md"), root) == "Spanish::Vocab"


def test_deck_name_deep_nesting():
    root = Path("/cards")
    assert _deck_name_from_path(
        Path("/cards/languages/spanish/grammar.md"), root
    ) == "Languages::Spanish::Grammar"


def test_deck_name_underscores_and_hyphens():
    root = Path("/cards")
    assert _deck_name_from_path(
        Path("/cards/web_dev/http-basics.md"), root
    ) == "Web Dev::Http Basics"


def test_collect_files_directory(tmp_path):
    (tmp_path / "a.md").write_text("# A\n")
    (tmp_path / "b.md").write_text("# B\n")
    (tmp_path / "not_md.txt").write_text("nope\n")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.md").write_text("# C\n")

    files, root = _collect_files(tmp_path)
    assert root == tmp_path
    assert len(files) == 3
    names = [f.name for f in files]
    assert "a.md" in names
    assert "b.md" in names
    assert "c.md" in names
    assert "not_md.txt" not in names
