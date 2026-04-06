import os
import re
import tempfile
import uuid
from dataclasses import dataclass, field

from remember.anki_client import (
    AnkiNote,
    add_note,
    delete_notes,
    ensure_deck,
    find_synced_notes,
    get_notes_info,
    strip_html,
    update_note_fields,
)
from remember.parser import InsightCard, parse_insights


@dataclass
class SyncResult:
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    orphaned: int = 0
    deleted: int = 0
    pulled: int = 0
    stamped: int = 0
    errors: list[str] = field(default_factory=list)


def _stamp_ids(markdown_file: str, cards: list[InsightCard], verbose: bool) -> int:
    """Insert generated IDs into the markdown file for cards missing them.

    Returns the number of cards stamped.
    """
    unstamped = [c for c in cards if c.id is None]
    if not unstamped:
        return 0

    # Assign IDs to the unstamped cards
    for card in unstamped:
        card.id = uuid.uuid4().hex[:8]
        _log(verbose, f"  [stamp]  {card.id}: {card.front}")

    # Build a lookup from H2 heading (first line of front) to generated ID
    headings_to_stamp = {c.front.split("\n")[0]: c.id for c in unstamped}

    with open(markdown_file, encoding="utf-8") as f:
        content = f.read()

    # Insert ID lines just before the --- separator for matching cards
    lines = content.split("\n")
    new_lines = []
    current_heading = None
    for line in lines:
        m = re.match(r"^## (.+)$", line)
        if m and m.group(1).strip() in headings_to_stamp:
            current_heading = m.group(1).strip()

        if current_heading and re.match(r"^---\s*$", line.strip()):
            card_id = headings_to_stamp.pop(current_heading)
            new_lines.append(f"<!-- id: {card_id} -->")
            current_heading = None

        new_lines.append(line)

    # Atomic write
    dir_name = os.path.dirname(os.path.abspath(markdown_file))
    with tempfile.NamedTemporaryFile(
        mode="w", dir=dir_name, suffix=".md", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write("\n".join(new_lines))
        tmp_path = tmp.name
    os.replace(tmp_path, markdown_file)

    return len(unstamped)


def _write_anki_to_markdown(markdown_file: str, card_id: str, front: str, back: str) -> None:
    """Replace a card's content in the markdown file with Anki's version."""
    with open(markdown_file, encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    new_lines = []
    i = 0
    while i < len(lines):
        # Look for the ID comment matching this card
        if re.match(rf"^<!--\s*id:\s*{re.escape(card_id)}\s*-->$", lines[i].strip()):
            # Walk backward to find the ## heading
            heading_idx = next(
                j for j in range(i - 1, -1, -1) if re.match(r"^## ", lines[j])
            )
            # Remove everything from heading to before this ID line
            new_lines = new_lines[:heading_idx]

            # Write new front: heading is first line, rest follows
            front_lines = front.split("\n")
            new_lines.append(f"## {front_lines[0]}")
            for fl in front_lines[1:]:
                new_lines.append(fl)
            new_lines.append(f"<!-- id: {card_id} -->")
            new_lines.append("---")
            new_lines.append(back)

            # Skip ahead past the old --- and back content to the next ## or EOF
            i += 1
            # Skip past ---
            while i < len(lines) and not re.match(r"^---\s*$", lines[i].strip()):
                i += 1
            i += 1  # skip the --- itself
            # Skip past old back content until next ## or EOF
            while i < len(lines) and not re.match(r"^## ", lines[i]):
                i += 1
            continue

        new_lines.append(lines[i])
        i += 1

    # Atomic write
    dir_name = os.path.dirname(os.path.abspath(markdown_file))
    with tempfile.NamedTemporaryFile(
        mode="w", dir=dir_name, suffix=".md", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write("\n".join(new_lines))
        tmp_path = tmp.name
    os.replace(tmp_path, markdown_file)


_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_DIM = "\033[2m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


def _color_diff(old: str, new: str, old_label: str, new_label: str) -> str:
    """Show a unified-style diff between two strings with color."""
    old_lines = old.split("\n")
    new_lines = new.split("\n")
    out = []
    out.append(f"  {_DIM}{old_label}{_RESET}")
    for line in old_lines:
        out.append(f"  {_RED}- {line}{_RESET}")
    out.append(f"  {_DIM}{new_label}{_RESET}")
    for line in new_lines:
        out.append(f"  {_GREEN}+ {line}{_RESET}")
    return "\n".join(out)


def _prompt_conflict(card_id: str, card_front: str, note: "AnkiNote", card: InsightCard) -> str:
    """Show conflict diff and prompt user. Returns 'm', 'a', or 's'."""
    heading = card_front.split("\n")[0]
    print(f"\n  {_BOLD}Conflict:{_RESET} {card_id} — \"{heading}\"")
    print(f"  {_DIM}Anki note was modified after your last file save.{_RESET}\n")
    if note.front != card.front:
        print(f"  {_YELLOW}Front:{_RESET}")
        print(_color_diff(card.front, note.front, "markdown", "anki"))
        print()
    if note.back != card.back:
        print(f"  {_YELLOW}Back:{_RESET}")
        print(_color_diff(card.back, note.back, "markdown", "anki"))
        print()
    try:
        answer = input(f"  Keep [{_BOLD}m{_RESET}]arkdown / [{_BOLD}a{_RESET}]nki / [{_BOLD}s{_RESET}]kip? ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        answer = "s"
        print()
    if answer in ("m", "a", "s"):
        return answer
    return "s"


def sync(
    markdown_file: str,
    deck: str = "Life Insights",
    verbose: bool = False,
) -> SyncResult:
    cards = parse_insights(markdown_file)
    if not cards:
        print("No cards found in markdown file.")
        return SyncResult()

    result = SyncResult()

    # Stamp IDs on cards that don't have them
    result.stamped = _stamp_ids(markdown_file, cards, verbose)
    if result.stamped > 0:
        print(f"{result.stamped} card(s) stamped with new IDs")
        # Re-parse to get clean state from the updated file
        cards = parse_insights(markdown_file)

    ensure_deck(deck)

    note_ids = find_synced_notes(deck)
    existing = get_notes_info(note_ids)
    anki_map: dict[str, AnkiNote] = {note.card_id: note for note in existing}
    file_mtime = os.path.getmtime(markdown_file)

    for card in cards:
        try:
            if card.id not in anki_map:
                _log(verbose, f"  [create] {card.id}: {card.front}")
                add_note(deck, card.front, card.back, card.id)
                result.created += 1
            else:
                note = anki_map[card.id]
                if strip_html(note.front) != strip_html(card.front) or strip_html(note.back) != strip_html(card.back):
                    anki_is_newer = note.mod > file_mtime
                    if anki_is_newer:
                        choice = _prompt_conflict(card.id, card.front, note, card)
                        if choice == "m":
                            _log(verbose, f"  [update] {card.id}: {card.front}")
                            update_note_fields(note.note_id, card.front, card.back)
                            result.updated += 1
                        elif choice == "a":
                            _log(verbose, f"  [pull]   {card.id}: {card.front}")
                            _write_anki_to_markdown(markdown_file, card.id, note.front, note.back)
                            result.pulled += 1
                        else:
                            _log(verbose, f"  [skip]   {card.id}: {card.front}")
                            result.unchanged += 1
                    else:
                        _log(verbose, f"  [update] {card.id}: {card.front}")
                        update_note_fields(note.note_id, card.front, card.back)
                        result.updated += 1
                else:
                    _log(verbose, f"  [skip]   {card.id}: {card.front}")
                    result.unchanged += 1
        except RuntimeError as e:
            result.errors.append(f"{card.id}: {e}")
            _log(verbose, f"  [error]  {card.id}: {e}")

    markdown_ids = {card.id for card in cards}
    orphans = [note for note in existing if note.card_id not in markdown_ids]
    result.orphaned = len(orphans)

    if orphans:
        print(f"\n{len(orphans)} orphaned card(s) found (in Anki but not in markdown):")
        for note in orphans:
            print(f"  {note.card_id}: {note.front}")
        try:
            answer = input("\nDelete orphaned cards from Anki? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = "n"
            print()
        if answer == "y":
            delete_notes([note.note_id for note in orphans])
            result.deleted = len(orphans)
            print(f"  Deleted {result.deleted} orphaned card(s).")

    print(
        f"{result.created} created, {result.updated} updated, "
        f"{result.pulled} pulled, {result.unchanged} unchanged, "
        f"{result.orphaned} orphaned, {result.deleted} deleted, "
        f"{result.stamped} stamped"
    )
    if result.errors:
        print(f"{len(result.errors)} error(s):")
        for err in result.errors:
            print(f"  {err}")
    return result


def _log(verbose: bool, message: str) -> None:
    if verbose:
        print(message)
