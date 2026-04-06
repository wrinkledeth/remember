import argparse
import sys
from pathlib import Path

from remember.config import load_config


def _deck_name_from_path(file_path: Path, root: Path) -> str:
    """Derive Anki deck name from file path relative to root directory.

    cards/spanish/vocab.md with root=cards -> Spanish::Vocab
    cards/cooking.md with root=cards -> Cooking
    """
    relative = file_path.relative_to(root)
    parts = list(relative.parent.parts) + [relative.stem]
    return "::".join(p.replace("_", " ").replace("-", " ").title() for p in parts)


def _collect_files(path: Path) -> tuple[list[Path], Path]:
    """Return (list of .md files, root directory) for a path."""
    if path.is_file():
        return [path], path.parent
    if path.is_dir():
        files = sorted(path.rglob("*.md"))
        return files, path
    print(f"Error: {path} is not a file or directory.")
    sys.exit(1)


def _resolve_cards_dir() -> Path:
    """Resolve cards directory from remember.toml."""
    config = load_config()
    if "cards_dir" not in config:
        print("Error: No cards_dir in remember.toml. Create one with:")
        print()
        print('  cards_dir = "./cards"')
        sys.exit(1)
    target = Path(config["cards_dir"])
    if not target.exists():
        print(f"Error: {target} does not exist.")
        sys.exit(1)
    return target


def _run_sync(verbose: bool = False) -> None:
    from remember.sync import sync

    target = _resolve_cards_dir()
    files, root = _collect_files(target)

    if not files:
        print(f"No .md files found in {target}")
        sys.exit(1)

    for file_path in files:
        deck = _deck_name_from_path(file_path, root)
        if len(files) > 1:
            print(f"\n--- {file_path.relative_to(root)} → {deck} ---")
        sync(
            markdown_file=str(file_path),
            deck=deck,
            verbose=verbose,
        )


def _run_pull(deck: str, verbose: bool = False) -> None:
    from remember.pull import pull

    target = _resolve_cards_dir()
    pull(deck=deck, cards_dir=target, verbose=verbose)


def _run_status(verbose: bool = False) -> None:
    from remember.status import status

    target = _resolve_cards_dir()
    files, root = _collect_files(target)

    if not files:
        print(f"No .md files found in {target}")
        sys.exit(1)

    status(files, root, verbose=verbose)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync flashcards from markdown to Anki"
    )
    subparsers = parser.add_subparsers(dest="command")

    sync_parser = subparsers.add_parser("push", help="Push cards to Anki")
    sync_parser.add_argument("--verbose", action="store_true", help="Print detailed per-card actions")

    pull_parser = subparsers.add_parser("pull", help="Pull cards from an Anki deck into markdown")
    pull_parser.add_argument("deck", help="Anki deck name (e.g. \"Spanish::Vocab\")")
    pull_parser.add_argument("--verbose", action="store_true", help="Print detailed per-card actions")

    status_parser = subparsers.add_parser("status", help="Show sync status without changes")
    status_parser.add_argument("--verbose", action="store_true", help="Show individual card details")

    args = parser.parse_args()

    if args.command == "push":
        _run_sync(verbose=args.verbose)
    elif args.command == "pull":
        _run_pull(deck=args.deck, verbose=args.verbose)
    elif args.command == "status":
        _run_status(verbose=args.verbose)
    else:
        parser.print_help()
