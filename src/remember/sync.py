from dataclasses import dataclass, field

from remember.anki_client import (
    AnkiNote,
    add_note,
    ensure_deck,
    find_synced_notes,
    get_notes_info,
    update_note_fields,
    update_tags,
)
from remember.parser import parse_insights


@dataclass
class SyncResult:
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    orphaned: int = 0
    errors: list[str] = field(default_factory=list)


def sync(
    markdown_file: str,
    deck: str = "Life Insights",
    dry_run: bool = False,
    verbose: bool = False,
) -> SyncResult:
    cards = parse_insights(markdown_file)
    if not cards:
        print("No cards found in markdown file.")
        return SyncResult()

    ensure_deck(deck)

    note_ids = find_synced_notes(deck)
    existing = get_notes_info(note_ids)
    anki_map: dict[str, AnkiNote] = {note.card_id: note for note in existing}

    result = SyncResult()

    for card in cards:
        try:
            if card.id not in anki_map:
                _log(verbose, f"  [create] {card.id}: {card.front}")
                if not dry_run:
                    add_note(deck, card.front, card.back, card.id, card.tags)
                result.created += 1
            else:
                note = anki_map[card.id]
                fields_changed = note.front != card.front or note.back != card.back
                tags_changed = sorted(note.tags) != sorted(card.tags)

                if fields_changed or tags_changed:
                    _log(verbose, f"  [update] {card.id}: {card.front}")
                    if not dry_run:
                        if fields_changed:
                            update_note_fields(note.note_id, card.front, card.back)
                        if tags_changed:
                            update_tags(note.note_id, card.id, note.tags, card.tags)
                    result.updated += 1
                else:
                    _log(verbose, f"  [skip]   {card.id}: {card.front}")
                    result.unchanged += 1
        except RuntimeError as e:
            result.errors.append(f"{card.id}: {e}")
            _log(verbose, f"  [error]  {card.id}: {e}")

    markdown_ids = {card.id for card in cards}
    for note in existing:
        if note.card_id not in markdown_ids:
            print(f"  [orphan] {note.card_id}: {note.front} (in Anki but not in markdown)")
            result.orphaned += 1

    prefix = "[dry-run] " if dry_run else ""
    print(
        f"{prefix}{result.created} created, {result.updated} updated, "
        f"{result.unchanged} unchanged, {result.orphaned} orphaned"
    )
    if result.errors:
        print(f"{len(result.errors)} error(s):")
        for err in result.errors:
            print(f"  {err}")
    return result


def _log(verbose: bool, message: str) -> None:
    if verbose:
        print(message)
