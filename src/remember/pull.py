import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from remember.anki_client import (
    ID_TAG_PREFIX,
    add_tags,
    find_notes_in_deck,
    get_deck_names,
    get_notes_info,
    strip_html,
)


@dataclass
class PullResult:
    pulled: int = 0
    skipped_non_basic: int = 0
    skipped_media: int = 0
    already_tracked: int = 0
    errors: list[str] = field(default_factory=list)

    def merge(self, other: "PullResult") -> None:
        self.pulled += other.pulled
        self.skipped_non_basic += other.skipped_non_basic
        self.skipped_media += other.skipped_media
        self.already_tracked += other.already_tracked
        self.errors.extend(other.errors)


_MEDIA_PATTERN = re.compile(r"<img|(\[sound:)", re.IGNORECASE)


def _has_media(text: str) -> bool:
    return bool(_MEDIA_PATTERN.search(text))


def _card_to_markdown(card_id: str, front: str, back: str) -> str:
    front = strip_html(front)
    back = strip_html(back)
    return f"## {front}\n<!-- id: {card_id} -->\n---\n{back}\n\n"


def file_path_from_deck(deck: str, cards_dir: Path) -> Path:
    parts = deck.split("::")
    parts = [p.strip().lower().replace(" ", "-") for p in parts]
    path_parts = parts[:-1]
    filename = parts[-1] + ".md"
    return cards_dir / Path(*path_parts, filename) if path_parts else cards_dir / filename


def _local_ids(cards_dir: Path) -> set[str]:
    """Scan all .md files in cards_dir for <!-- id: xxx --> and return the set of IDs."""
    ids: set[str] = set()
    for md_file in cards_dir.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
        except OSError:
            continue
        ids.update(re.findall(r"<!--\s*id:\s*(\w+)\s*-->", content))
    return ids


def _pull_single_deck(
    deck: str, cards_dir: Path, local_ids: set[str], verbose: bool = False,
) -> PullResult:
    """Pull cards from exactly one deck (no subdecks) into a single markdown file."""
    result = PullResult()

    note_ids = find_notes_in_deck(deck, exact=True)
    if not note_ids:
        return result

    notes = get_notes_info(note_ids)

    to_pull = []
    for note in notes:
        if note.model_name != "Basic" and (not note.front or not note.back):
            if verbose:
                print(f"  [skip] non-Basic without Front/Back ({note.model_name}): {note.front[:50]}")
            result.skipped_non_basic += 1
            continue

        if _has_media(note.front) or _has_media(note.back):
            if verbose:
                print(f"  [skip] contains media: {note.front[:50]}")
            result.skipped_media += 1
            continue

        if note.card_id and note.card_id in local_ids:
            if verbose:
                print(f"  [skip] already tracked: {note.card_id}: {note.front[:50]}")
            result.already_tracked += 1
            continue

        to_pull.append(note)

    if not to_pull:
        return result

    # Generate IDs (reuse existing tag if card was tagged but file is missing)
    pending_tags: list[tuple[int, str]] = []
    cards_content = []
    for note in to_pull:
        card_id = note.card_id if note.card_id else uuid.uuid4().hex[:8]
        if not note.card_id:
            pending_tags.append((note.note_id, f"{ID_TAG_PREFIX}{card_id}"))
        cards_content.append((card_id, note.front, note.back))
        if verbose:
            print(f"  [pull]  {card_id}: {note.front[:50]}")
        result.pulled += 1

    if not cards_content:
        return result

    # Build markdown and write file FIRST
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

    print(f"  Wrote {result.pulled} card(s) to {output_path}")

    # Tag in Anki AFTER file write succeeds
    for note_id, tag in pending_tags:
        try:
            add_tags([note_id], tag)
        except RuntimeError as e:
            result.errors.append(f"Failed to tag note {note_id}: {e}")

    return result


def pull(deck: str, cards_dir: Path, verbose: bool = False) -> PullResult:
    """Pull cards from a deck and all its subdecks into markdown files."""
    all_decks = get_deck_names()
    # Find this deck + all subdecks
    matching = sorted(
        d for d in all_decks
        if d == deck or d.startswith(deck + "::")
    )

    if not matching:
        print(f"No deck found matching \"{deck}\".")
        return PullResult()

    local = _local_ids(cards_dir)

    total = PullResult()
    for subdeck in matching:
        if verbose:
            print(f"\n--- {subdeck} ---")
        result = _pull_single_deck(subdeck, cards_dir, local, verbose=verbose)
        total.merge(result)

    _print_summary(total)
    return total


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
