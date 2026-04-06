# remember

Sync life insight flashcards from a markdown file to Anki via spaced repetition.

## Prerequisites

- [Anki](https://apps.ankiweb.net/) with [AnkiConnect](https://ankiweb.net/shared/info/2055492159) installed and running
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
git clone git@github.com:wrinkledeth/remember.git
cd remember
uv sync
```

## Usage

```bash
uv run remember insights.md                        # sync to deck "Insights"
uv run remember insights.md --dry-run --verbose     # preview changes
uv run remember relationships.md                    # sync to deck "Relationships"
```

## Markdown Format

See [`INSIGHT_FORMAT_SPEC.md`](INSIGHT_FORMAT_SPEC.md) for the full spec.

```markdown
# Life Insights

## Card front text
<!-- id: 001 -->
Card back text. Multiple paragraphs allowed.

## Next card
<!-- id: 002 -->
Next card back.
```

Each `##` heading is a card front. The metadata comment (`<!-- id: NNN -->`) must follow immediately. Everything after the metadata until the next `##` is the card back. The filename becomes the Anki deck name (`relationships.md` → "Relationships").

## Sync Behavior

The markdown file is the source of truth. Anki is just the delivery mechanism. The sync is additive — it never deletes cards or resets study progress.

| Scenario                      | Action                            |
| ----------------------------- | --------------------------------- |
| Card in markdown, not in Anki | **Create**                        |
| Card in both, content changed | **Update** (preserves scheduling) |
| Card in both, identical       | **Skip**                          |
| Card in Anki, not in markdown | **Warn** (never deletes)          |
