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


def parse_insights(filepath: str) -> list[InsightCard]:
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    cards = []
    # Split on H2 headings; produces [preamble, front1, body1, front2, body2, ...]
    sections = re.split(r"^## (.+)$", content, flags=re.MULTILINE)

    for i in range(1, len(sections), 2):
        heading = sections[i].strip()
        body = sections[i + 1] if i + 1 < len(sections) else ""

        lines = body.split("\n")

        # Find the --- separator
        sep_idx = None
        for j, line in enumerate(lines):
            if _SEPARATOR.match(line.strip()):
                sep_idx = j
                break

        if sep_idx is None:
            warnings.warn(f"Card '{heading}': missing --- separator, skipping")
            continue

        # Front = heading + lines before separator (excluding ID comment and blanks)
        card_id = None
        front_lines = [heading]
        for line in lines[:sep_idx]:
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
        back = "\n".join(lines[sep_idx + 1 :]).strip()

        cards.append(InsightCard(id=card_id, front=front, back=back))

    return cards
