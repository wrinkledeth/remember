# remember

A CLI that syncs flashcards from a markdown file to [Anki](https://apps.ankiweb.net/) via [AnkiConnect](https://ankiweb.net/shared/info/2055492159).

Write cards in markdown. Run `remember`. They show up in Anki with spaced repetition — no manual card creation.

## Quick start

```bash
git clone git@github.com:wrinkledeth/remember.git
cd remember
uv sync
```

Requires [Anki](https://apps.ankiweb.net/) running with [AnkiConnect](https://ankiweb.net/shared/info/2055492159), and [uv](https://docs.astral.sh/uv/).

## Usage

```bash
uv run remember insights.md                     # sync to deck "Insights"
uv run remember relationships.md                # sync to deck "Relationships"
uv run remember insights.md --dry-run --verbose # preview without changes
```

The filename becomes the deck name.

## Card format

```markdown
# Life Insights

<!-- Section: Relationships -->

## When she's venting about her day
and I feel the urge to jump in with solutions
---
Just hold space. She's not asking me to solve it.
The urge to fix is about my discomfort with her discomfort.

## I just got critical feedback and my chest is tight.
---
The ego is conflating the work with the self.
The feedback is about the artifact, not about my worth.
```

`##` starts a card. `---` separates front from back. Everything else (comments, prose) is ignored. Fronts and backs can be multiple lines.

IDs are auto-generated on first sync and written back into the file as `<!-- id: xxxxxxxx -->` comments. You never need to manage them.

See [`INSIGHT_FORMAT_SPEC.md`](INSIGHT_FORMAT_SPEC.md) for the full spec.

## How sync works

The markdown file is the source of truth. Anki is just the delivery mechanism.

| Scenario | Action |
|---|---|
| New card in markdown | **Create** in Anki |
| Card edited in markdown | **Update** in Anki (preserves scheduling) |
| Card unchanged | **Skip** |
| Card removed from markdown | **Warn** (never auto-deletes from Anki) |

## Good Anki Card Design
