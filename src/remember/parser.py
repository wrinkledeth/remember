import re
import warnings
from dataclasses import dataclass


@dataclass
class InsightCard:
    id: str
    front: str
    back: str


_METADATA_RE = re.compile(
    r'^<!--\s*id:\s*(\S+?)\s*-->$'
)


def parse_insights(filepath: str) -> list[InsightCard]:
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    cards = []
    # Split on H2 headings; produces [preamble, front1, body1, front2, body2, ...]
    sections = re.split(r'^## (.+)$', content, flags=re.MULTILINE)

    for i in range(1, len(sections), 2):
        front = sections[i].strip()
        body = sections[i + 1] if i + 1 < len(sections) else ""

        lines = body.split('\n')

        # Find the first non-empty line — must be the metadata comment
        first_nonempty = next(
            (line.strip() for line in lines if line.strip()), None
        )
        if first_nonempty is None:
            warnings.warn(f"Card '{front}' (no metadata): skipping")
            continue

        match = _METADATA_RE.match(first_nonempty)
        if not match:
            warnings.warn(
                f"Card '{front}': malformed metadata line '{first_nonempty}', skipping"
            )
            continue

        card_id = match.group(1)

        # Back is everything after the metadata line
        metadata_idx = next(j for j, line in enumerate(lines) if line.strip() == first_nonempty)
        back = '\n'.join(lines[metadata_idx + 1:]).strip()

        cards.append(InsightCard(id=card_id, front=front, back=back))

    return cards
