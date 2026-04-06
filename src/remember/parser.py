import re
import warnings
from dataclasses import dataclass


@dataclass
class InsightCard:
    id: str | None
    front: str
    back: str


_METADATA_RE = re.compile(r"^<!--\s*id:\s*(\S+?)\s*-->$")
_SEPARATOR = re.compile(r"^---\s*$")
_HEADING_RE = re.compile(r"^## (.+)$")


def parse_insights(filepath: str) -> list[InsightCard]:
    with open(filepath, encoding="utf-8") as f:
        all_lines = f.readlines()

    # Find all H2 heading positions
    headings: list[tuple[int, str]] = []
    for line_num, line in enumerate(all_lines):
        m = _HEADING_RE.match(line.rstrip("\n"))
        if m:
            headings.append((line_num, m.group(1).strip()))

    cards = []
    for idx, (line_num, heading) in enumerate(headings):
        # Body extends from after the heading to the next heading (or EOF)
        body_start = line_num + 1
        body_end = headings[idx + 1][0] if idx + 1 < len(headings) else len(all_lines)
        body_lines = [l.rstrip("\n") for l in all_lines[body_start:body_end]]

        # Find the --- separator
        sep_idx = None
        for j, line in enumerate(body_lines):
            if _SEPARATOR.match(line.strip()):
                sep_idx = j
                break

        if sep_idx is None:
            warnings.warn(
                f"{filepath}:{line_num + 1}: Card '{heading}' is missing --- separator, skipping"
            )
            continue

        # Front = heading + lines before separator (excluding ID comment and blanks)
        card_id = None
        front_lines = [heading]
        for line in body_lines[:sep_idx]:
            stripped = line.strip()
            if not stripped:
                continue
            match = _METADATA_RE.match(stripped)
            if match:
                card_id = match.group(1)
                continue
            front_lines.append(stripped)

        front = "\n".join(front_lines).strip()

        # Back = everything after separator
        back = "\n".join(body_lines[sep_idx + 1 :]).strip()

        cards.append(InsightCard(id=card_id, front=front, back=back))

    return cards
