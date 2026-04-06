# Remember

A CLI tool that syncs life insight flashcards from a canonical markdown file to Anki via AnkiConnect.

## Project Philosophy

This tool bridges a single markdown file (the source of truth for personal life insights) with an Anki deck for spaced repetition. The markdown file is human-readable and portable. Anki is just the delivery mechanism. The sync is additive and non-destructive — it never deletes cards or resets study progress.

## Architecture

- **Language:** Python 3.12+
- **Dependencies:** Minimal. `requests` for AnkiConnect HTTP calls. No frameworks.
- **Entry point:** `sync.py` — CLI script, no subcommands for now. Run it, it syncs.
- **Key modules:**
  - `parser.py` — Parses the markdown file into a list of card objects (`id`, `front`, `back`, `tags`)
  - `anki_client.py` — Thin wrapper around AnkiConnect's REST API (localhost:8765)
  - `sync.py` — Orchestrates: parse markdown → query Anki → diff → create/update

## Markdown Format

See `INSIGHT_FORMAT_SPEC.md` for the full spec. Summary:

```markdown
# Life Insights

## Card front text (H2 heading)
<!-- id: 001 | tags: mindset, relationships -->
Card back text. Multiple lines/paragraphs allowed.
Full markdown supported in the back.

## Next card front
<!-- id: 002 | tags: career -->
Next card back.
```

- H1 is the document title (ignored by parser)
- Each H2 starts a new card — heading text = front
- First line after H2 must be `<!-- id: NNN | tags: tag1, tag2 -->` (tags optional)
- Everything between the metadata comment and the next H2 = back
- Back text should be stripped of leading/trailing whitespace

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
- `addTags` / `removeTags` — sync tags if they changed
- `changeDeck` — not used (single deck)

### ID Tracking Strategy

Store the insight ID (from the markdown `<!-- id: NNN -->`) in the Anki note's tags as `insight-id::NNN`. This avoids needing a custom note type — we use the built-in `Basic` type and track IDs via tags. The sync engine queries `tag:insight-id::*` within the target deck to find existing synced cards.

## Sync Logic (Critical)

```
1. Parse markdown → list of InsightCards
2. Query Anki for all notes in target deck with tag `insight-id::*`
3. Build a map: { insight_id → anki_note_id }
4. For each InsightCard:
   a. If insight_id NOT in map → addNote (create)
   b. If insight_id IN map AND content differs → updateNoteFields (update)
   c. If insight_id IN map AND content identical → skip
5. Cards in Anki but NOT in markdown → log a warning, do NOT delete
6. Print summary: X created, Y updated, Z unchanged, W orphaned
```

## CLI Interface

```
python sync.py <markdown_file> [--deck "Life Insights"] [--dry-run] [--verbose]
```

- `<markdown_file>` — path to the insights markdown file (required)
- `--deck` — Anki deck name (default: "Life Insights")
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
- If a card has malformed metadata, warn and skip it — don't crash the whole sync

## Future (Do Not Build Yet)

- Obsidian plugin port (TypeScript)
- LLM-powered insight distillation (separate tool)
- Tag-based filtered sync to multiple decks
- Bi-directional sync (Anki → markdown)
