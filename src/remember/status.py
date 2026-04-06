import os
from pathlib import Path

from remember.anki_client import AnkiNote, find_synced_notes, get_notes_info, strip_html
from remember.parser import parse_insights


def _deck_name_from_path(file_path: Path, root: Path) -> str:
    relative = file_path.relative_to(root)
    parts = list(relative.parent.parts) + [relative.stem]
    return "::".join(p.replace("_", " ").replace("-", " ").title() for p in parts)


_DIM = "\033[2m"
_BOLD = "\033[1m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_RESET = "\033[0m"


def status(files: list[Path], root: Path, verbose: bool = False) -> None:
    """Show sync status for each file without making any changes."""
    total_new = 0
    total_changed = 0
    total_unchanged = 0
    total_orphaned = 0
    total_unstamped = 0

    for file_path in files:
        deck = _deck_name_from_path(file_path, root)
        cards = parse_insights(str(file_path))

        unstamped = sum(1 for c in cards if c.id is None)
        stamped_cards = [c for c in cards if c.id is not None]

        try:
            note_ids = find_synced_notes(deck)
            existing = get_notes_info(note_ids)
        except RuntimeError as e:
            print(f"{_RED}{deck}{_RESET}: {e}")
            continue

        anki_map: dict[str, AnkiNote] = {note.card_id: note for note in existing}

        new = 0
        changed = 0
        unchanged = 0

        for card in stamped_cards:
            if card.id not in anki_map:
                new += 1
                if verbose:
                    print(f"  {_GREEN}[new]{_RESET}     {card.id}: {card.front}")
            else:
                note = anki_map[card.id]
                if strip_html(note.front) != strip_html(card.front) or strip_html(note.back) != strip_html(card.back):
                    changed += 1
                    if verbose:
                        print(f"  {_YELLOW}[changed]{_RESET} {card.id}: {card.front}")
                else:
                    unchanged += 1

        markdown_ids = {c.id for c in stamped_cards}
        orphaned = [n for n in existing if n.card_id not in markdown_ids]

        # Print deck summary
        rel = file_path.relative_to(root)
        parts = []
        if new:
            parts.append(f"{_GREEN}{new} new{_RESET}")
        if changed:
            parts.append(f"{_YELLOW}{changed} changed{_RESET}")
        if orphaned:
            parts.append(f"{_RED}{len(orphaned)} orphaned{_RESET}")
        if unstamped:
            parts.append(f"{unstamped} unstamped")
        parts.append(f"{unchanged} synced")

        print(f"{_BOLD}{deck}{_RESET} {_DIM}({rel}){_RESET}: {', '.join(parts)}")

        if verbose and orphaned:
            for note in orphaned:
                print(f"  {_RED}[orphan]{_RESET}  {note.card_id}: {note.front}")

        total_new += new
        total_changed += changed
        total_unchanged += unchanged
        total_orphaned += len(orphaned)
        total_unstamped += unstamped

    if len(files) > 1:
        print(f"\n{_BOLD}Total{_RESET}: {total_new + total_changed + total_unchanged + total_unstamped} cards across {len(files)} files")
        parts = []
        if total_new:
            parts.append(f"{total_new} new")
        if total_changed:
            parts.append(f"{total_changed} changed")
        if total_orphaned:
            parts.append(f"{total_orphaned} orphaned")
        if total_unstamped:
            parts.append(f"{total_unstamped} unstamped")
        parts.append(f"{total_unchanged} synced")
        print(f"  {', '.join(parts)}")
