import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from remember.anki_client import (
    ID_TAG_PREFIX,
    add_tags,
    find_notes_in_deck,
    get_notes_info,
)


@dataclass
class PullResult:
    pulled: int = 0
    skipped_non_basic: int = 0
    skipped_media: int = 0
    already_tracked: int = 0
    errors: list[str] = field(default_factory=list)


_MEDIA_PATTERN = re.compile(r"<img|(\[sound:)", re.IGNORECASE)


def _has_media(text: str) -> bool:
    return bool(_MEDIA_PATTERN.search(text))


def _card_to_markdown(card_id: str, front: str, back: str) -> str:
    return f"## {front}\n<!-- id: {card_id} -->\n---\n{back}\n\n"


def file_path_from_deck(deck: str, cards_dir: Path) -> Path:
    parts = deck.split("::")
    parts = [p.strip().lower().replace(" ", "-") for p in parts]
    path_parts = parts[:-1]
    filename = parts[-1] + ".md"
    return cards_dir / Path(*path_parts, filename) if path_parts else cards_dir / filename


def pull(deck: str, cards_dir: Path, verbose: bool = False) -> PullResult:
    result = PullResult()

    note_ids = find_notes_in_deck(deck)
    if not note_ids:
        print(f"No notes found in deck \"{deck}\".")
        return result

    notes = get_notes_info(note_ids)

    to_pull = []
    for note in notes:
        if note.model_name != "Basic":
            if verbose:
                print(f"  [skip] non-Basic note type ({note.model_name}): {note.front[:50]}")
            result.skipped_non_basic += 1
            continue

        if _has_media(note.front) or _has_media(note.back):
            if verbose:
                print(f"  [skip] contains media: {note.front[:50]}")
            result.skipped_media += 1
            continue

        if note.card_id:
            if verbose:
                print(f"  [skip] already tracked: {note.card_id}: {note.front[:50]}")
            result.already_tracked += 1
            continue

        to_pull.append(note)

    if not to_pull:
        print("No new cards to pull.")
        _print_summary(result)
        return result

    # Generate IDs and tag in Anki
    cards_content = []
    for note in to_pull:
        card_id = uuid.uuid4().hex[:8]
        tag = f"{ID_TAG_PREFIX}{card_id}"
        try:
            add_tags([note.note_id], tag)
        except RuntimeError as e:
            result.errors.append(f"Failed to tag note {note.note_id}: {e}")
            continue
        cards_content.append((card_id, note.front, note.back))
        if verbose:
            print(f"  [pull]  {card_id}: {note.front[:50]}")
        result.pulled += 1

    if not cards_content:
        _print_summary(result)
        return result

    # Build markdown
    output_path = file_path_from_deck(deck, cards_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        markdown = "\n"
    else:
        title = deck.split("::")[-1].strip()
        markdown = f"# {title}\n\n"

    for card_id, front, back in cards_content:
        markdown += _card_to_markdown(card_id, front, back)

    with open(output_path, "a", encoding="utf-8") as f:
        f.write(markdown)

    print(f"Wrote {result.pulled} card(s) to {output_path}")
    _print_summary(result)
    return result


def _print_summary(result: PullResult) -> None:
    parts = [f"{result.pulled} pulled"]
    if result.skipped_non_basic:
        parts.append(f"{result.skipped_non_basic} skipped (non-Basic)")
    if result.skipped_media:
        parts.append(f"{result.skipped_media} skipped (media)")
    if result.already_tracked:
        parts.append(f"{result.already_tracked} already tracked")
    if result.errors:
        parts.append(f"{len(result.errors)} error(s)")
    print(", ".join(parts))
