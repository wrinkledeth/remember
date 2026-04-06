import argparse

from remember.sync import sync


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync life insight flashcards from markdown to Anki"
    )
    parser.add_argument("markdown_file", help="Path to the insights markdown file")
    parser.add_argument(
        "--deck",
        default="Life Insights",
        help='Anki deck name (default: "Life Insights")',
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed per-card actions",
    )

    args = parser.parse_args()
    sync(
        markdown_file=args.markdown_file,
        deck=args.deck,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )
