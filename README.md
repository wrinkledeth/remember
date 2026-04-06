# remember

Syncs life insight flashcards from a canonical markdown file to Anki via AnkiConnect.

## Prerequisites

- [Anki](https://apps.ankiweb.net/) with the [AnkiConnect](https://ankiweb.net/shared/info/2055492159) add-on installed and Anki running
- [uv](https://docs.astral.sh/uv/) for Python package management

## Setup

```bash
git clone <repo>
cd remember
uv sync
```

## Usage

```bash
uv run remember <markdown_file> [options]
```

**Options:**

| Flag | Description |
|---|---|
| `--deck "Life Insights"` | Target Anki deck name (default: `Life Insights`) |
| `--dry-run` | Preview what would be created/updated without making changes |
| `--verbose` | Print per-card actions during sync |

**Examples:**

```bash
# Basic sync
uv run remember insights.md

# Dry run to preview changes
uv run remember insights.md --dry-run --verbose

# Sync to a different deck
uv run remember insights.md --deck "Personal"
```

## Markdown Format

Cards live in a single markdown file. See `INSIGHT_FORMAT_SPEC.md` for the full spec.

```markdown
# Life Insights

## Card front text
<!-- id: 001 | tags: mindset, relationships -->
Card back text. Multiple paragraphs allowed.

## Next card
<!-- id: 002 | tags: career -->
Next card back.
```

- Each `##` heading is a card front
- The first line after the heading must be the `<!-- id: NNN | tags: ... -->` metadata comment
- Tags are optional
- Everything after the metadata line (until the next `##`) is the card back

## Sync Behavior

| Scenario | Action |
|---|---|
| Card in markdown, not in Anki | Create |
| Card in both, content changed | Update (preserves scheduling) |
| Card in both, content identical | Skip |
| Card in Anki, removed from markdown | Warn, no action (never auto-deletes) |

## Architecture

The markdown file is the single source of truth. Anki is the delivery mechanism. The sync is additive — it never deletes cards or resets study progress.

```
src/remember/
├── cli.py          # argparse entry point, calls sync()
├── parser.py       # parses markdown → list[InsightCard]
├── anki_client.py  # thin wrapper around AnkiConnect REST API
└── sync.py         # orchestrates: parse → query → diff → create/update
```

**ID tracking:** Each card's ID (from `<!-- id: NNN -->`) is stored in Anki as the tag `insight-id::NNN`. This avoids needing a custom note type — standard `Basic` notes are used and cards are matched by tag.

**Sync flow:**
1. Parse markdown → `list[InsightCard]`
2. Query Anki for all notes tagged `insight-id::*` in the target deck
3. Build a map `{ insight_id → anki_note_id }`
4. For each card: create if new, update if content changed, skip if identical
5. Log a warning for any Anki notes whose ID is no longer in the markdown

## Development

```bash
# Run tests
uv run pytest

# Run with verbose output
uv run pytest -v
```

## Notes

- `insights.md` is gitignored — it's your personal cards file, keep it wherever works for you
- `tests/fixtures/test_insights.md` intentionally contains a malformed card (no metadata) and a card with an empty back — these exist to exercise parser edge cases, not as real content
- AnkiConnect must be running (Anki open) for any sync to work; the CLI will give a clear error if it can't connect
- Cards are never deleted by the sync — removing a card from markdown leaves it in Anki and logs it as `[orphan]`. Delete manually in Anki if needed.
- The `Basic` note type is used with no customization. ID tracking is done entirely via tags (`insight-id::NNN`), so no custom note type or extra fields are required.

## Next Steps

- **`test_sync.py`** — unit tests for sync logic with mocked AnkiConnect responses
- **Tag-based filtered sync** — sync cards with specific tags to separate Anki decks
- **`--stats` flag** — show per-tag card counts and last-sync timestamp
- **Obsidian plugin** — TypeScript port that runs the sync from within Obsidian
- **LLM-powered distillation** — separate tool that drafts insight cards from journal entries or notes
