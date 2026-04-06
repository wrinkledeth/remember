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
# Flashcards

<!-- Section: Web Fundamentals -->

## What does the HTTP 503 status code mean?
---
Service Unavailable. 

## What does "mise en place" mean?
---
"Everything in its place."
```

`##` starts a card. `---` separates front from back. Everything else (comments, prose) is ignored. Fronts and backs can be multiple lines.

IDs are auto-generated on first sync and written back into the file as `<!-- id: xxxxxxxx -->` comments. You never need to manage them.

## How sync works

The markdown file is the source of truth. Anki is the delivery mechanism.

| Scenario | Action |
|---|---|
| New card in markdown | **Create** in Anki |
| Card edited in markdown | **Update** in Anki (preserves scheduling) |
| Card unchanged | **Skip** |
| Card edited in both (Anki is newer) | **Conflict** — interactive prompt |
| Card removed from markdown | **Orphan** — prompts to delete from Anki |

### Conflicts

When a card differs between markdown and Anki *and* the Anki note was modified more recently than the file, `remember` shows a colored diff and asks you to choose:

- **`m`** — keep **m**arkdown version (push to Anki)
- **`a`** — keep **a**nki version (pull back into markdown file)
- **`s`** — **s**kip (leave both as-is)

## Good card design

- **One idea per card.** Keep it direct and atomic.
- **Front = trigger.** A question, scenario, or cue — something you'd encounter in the wild.
- **Back = answer.** Short, direct. If you're writing a paragraph, you're explaining — not answering.
- **No orphan backs.** If the back doesn't make sense without reading the front, rewrite the front.
- **Use your own words.** Cards you write yourself stick better than ones you copy.