# remember

A CLI that syncs flashcards from markdown to [Anki](https://apps.ankiweb.net/) via [AnkiConnect](https://ankiweb.net/shared/info/2055492159).

Write cards in markdown. Run `remember`. They appear in Anki with spaced repetition. Your cards are plain text — version-controllable, portable, editable in any editor.

## Prerequisites

- [Anki](https://apps.ankiweb.net/) running with [AnkiConnect](https://ankiweb.net/shared/info/2055492159) installed
- [uv](https://docs.astral.sh/uv/)

## Quick start

```bash
git clone git@github.com:wrinkledeth/remember.git
cd remember
uv sync
```

Create a `remember.toml` in your project root:

```toml
cards_dir = "./cards"
```

Then sync:

```bash
uv run remember push
```

```
3 created, 0 updated, 0 pulled, 0 unchanged, 0 orphaned, 0 deleted, 3 stamped
```

## Usage

```bash
uv run remember status            # check what would change without syncing
uv run remember push              # push all cards to Anki
uv run remember pull "Deck Name"  # import an Anki deck into markdown
uv run remember push --verbose    # show per-card details
```

Directory structure maps to Anki's deck hierarchy:

```
cards/
  cooking.md                → Cooking
  spanish/
    vocab.md                → Spanish::Vocab
    grammar.md              → Spanish::Grammar
```

### `remember pull <deck>`

Imports cards from an existing Anki deck into a markdown file. Useful for bringing decks you already have into the markdown workflow.

```bash
uv run remember pull "Spanish::Vocab"
```

```
Wrote 15 card(s) to cards/spanish/vocab.md
15 pulled, 2 skipped (non-Basic), 1 skipped (media)
```

- Only pulls **Basic** note types. Non-Basic (Cloze, etc.) are skipped with a warning.
- Cards containing media (`<img`, `[sound:`) are skipped.
- Cards already tracked by `remember` (tagged with `insight-id::`) are skipped.
- New cards get an ID generated and tagged in Anki so future `push`es stay linked.
- If the output file already exists, new cards are appended.

### `remember status`

Shows a summary per deck — new, changed, orphaned, and synced card counts. Use `--verbose` to see individual cards.

```
Cooking (cooking.md): 2 new, 5 synced
Spanish::Vocab (spanish/vocab.md): 1 changed, 12 synced
Spanish::Grammar (spanish/grammar.md): 8 synced
```

## Card format

```markdown
## What does the HTTP 503 status code mean?
<!-- id: a3f8b2c1 -->
---
Service Unavailable. The server is temporarily unable to handle
the request, usually due to maintenance or overload.
Unlike 500, it implies the condition is temporary.

## What does "mise en place" mean?
<!-- id: 7e2d19f4 -->
---
"Everything in its place." Prep and organize all ingredients
before you start cooking.
```

`##` starts a card. `---` separates front from back. Everything else is ignored. Fronts and backs can be multiple lines.

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

When a card differs and the Anki note is newer than the file, `remember` shows a colored diff and asks:

- **`m`** — keep **m**arkdown (push to Anki)
- **`a`** — keep **a**nki (pull into markdown)
- **`s`** — **s**kip

## Roadmap

- [x] **Multi-file / directory sync** — directory structure mirrors Anki deck hierarchy
- [x] **`remember status`** — card counts per deck without syncing
- [ ] **Watch mode** — `remember --watch` re-syncs on file save
- [x] **Pull from Anki** — `remember pull <deck>` imports an Anki deck into markdown

## Card design tips

- **One idea per card.** Keep it direct and atomic.
- **Front = trigger.** A question, scenario, or cue.
- **Back = answer.** Short and direct. If you're writing a paragraph, you're explaining — not answering.
- **No orphan backs.** If the back doesn't make sense without the front, rewrite the front.
- **Use your own words.** Cards you write stick better than cards you copy.
