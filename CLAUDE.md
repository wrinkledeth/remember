# Remember

A CLI tool that syncs life insight flashcards from a canonical markdown file to Anki via AnkiConnect.

## Project Philosophy

This tool bridges a single markdown file (the source of truth for personal life insights) with an Anki deck for spaced repetition. The markdown file is human-readable and portable. Anki is just the delivery mechanism. The sync is additive and non-destructive — it never deletes cards or resets study progress.

## Architecture

- **Language:** Python 3.12+
- **Dependencies:** Minimal. `requests` for AnkiConnect HTTP calls. No frameworks.
- **Entry point:** `sync.py` — CLI script, no subcommands for now. Run it, it syncs.
- **Key modules:**
  - `parser.py` — Parses the markdown file into a list of card objects (`id`, `front`, `back`)
  - `anki_client.py` — Thin wrapper around AnkiConnect's REST API (localhost:8765)
  - `sync.py` — Orchestrates: parse markdown → query Anki → diff → create/update

## Markdown Format

See `INSIGHT_FORMAT_SPEC.md` for the full spec. Summary:

```markdown
# Life Insights

<!-- Section: Relationships -->

## When she's venting about her day
<!-- id: a3f8b2c1 -->
and I feel the urge to jump in with solutions
---
Just hold space. She's not asking me to solve it.

## Next card front
---
Next card back.
```

- H1 is the document title (ignored by parser)
- `##` starts a new card
- `---` separates front from back (required)
- Everything between `##` and `---` is the front (multi-line supported)
- Everything between `---` and the next `##` is the back (multi-line supported)
- `<!-- id: NNN -->` is **optional** — if missing, `remember sync` auto-generates an 8-char hex ID and writes it into the file after the `##` heading
- All other content (HTML comments, prose outside cards) is ignored by the parser
- Cards missing `---` are warned about and skipped
- Filename determines the Anki deck name (`relationships.md` → "Relationships")

## AnkiConnect Integration

- AnkiConnect runs at `http://localhost:8765`
- Target deck name: `Life Insights` (configurable via CLI arg or env var)
- Note type: `Basic` (Front / Back fields)
- Use AnkiConnect API version 6
- Cards are identified by a custom field or tag containing the insight ID for matching

### Key AnkiConnect Actions Used

- `findNotes` — query existing notes in the deck
- `notesInfo` — get full note details for diffing
- `addNote` — create new card
- `updateNoteFields` — update front/back text without resetting scheduling

### ID Tracking Strategy

Store the insight ID (from the markdown `<!-- id: NNN -->`) in the Anki note's tags as `insight-id::NNN`. This avoids needing a custom note type — we use the built-in `Basic` type and track IDs via tags. The sync engine queries `tag:insight-id::*` within the target deck to find existing synced cards.

## Sync Logic (Critical)

```
1. Parse markdown → list of InsightCards (cards without IDs get id=None)
2. Stamp: for any card with id=None, generate 8-char hex ID, write it into the markdown file (atomic write), re-parse
3. Query Anki for all notes in target deck with tag `insight-id::*`
4. Build a map: { insight_id → anki_note_id }
5. For each InsightCard:
   a. If insight_id NOT in map → addNote (create)
   b. If insight_id IN map AND content differs → updateNoteFields (update)
   c. If insight_id IN map AND content identical → skip
6. Cards in Anki but NOT in markdown → log a warning, do NOT delete
7. Print summary: X created, Y updated, Z unchanged, W orphaned, N stamped
```

## CLI Interface

```
remember <markdown_file> [--dry-run] [--verbose]
```

- `<markdown_file>` — path to the insights markdown file (required). Filename becomes the Anki deck name.
- `--dry-run` — show what would happen without making changes
- `--verbose` — print detailed per-card actions

## Testing

- Use `pytest` for unit tests
- `test_parser.py` — test markdown parsing with various edge cases:
  - Normal cards
  - Cards without tags
  - Multi-paragraph backs
  - Malformed metadata lines (should warn, not crash)
  - Empty backs
- `test_sync.py` — test sync logic with mocked AnkiConnect responses
- Include a `test_insights.md` fixture file with sample cards

## Code Style

- Type hints on all functions
- Dataclasses for structured data (InsightCard, SyncResult)
- No classes where functions suffice — keep it simple
- Descriptive variable names, minimal comments (code should be self-documenting)
- Handle errors gracefully: if AnkiConnect is not running, say so clearly
- If a card has no ID, auto-stamp it at sync time — don't require manual ID entry

## Future (Do Not Build Yet)

- Obsidian plugin port (TypeScript)
- LLM-powered insight distillation (separate tool)
- Tag-based filtered sync to multiple decks
- Bi-directional sync (Anki → markdown)
