# Claude Code Prompts — Remember CLI

Use these prompts in order. Each one builds on the previous step. Make sure CLAUDE.md and INSIGHT_FORMAT_SPEC.md are in the project root before starting.

---

## Prompt 1: Project setup + Parser

```
Read CLAUDE.md and INSIGHT_FORMAT_SPEC.md to understand the project.

Set up the project structure:
- Create a pyproject.toml with the project metadata and dependencies (requests, pytest)
- Create the package structure: remember/ with __init__.py, parser.py, anki_client.py, sync.py
- Create tests/ with __init__.py

Then build parser.py:
- Define an InsightCard dataclass with fields: id (str), front (str), back (str), tags (list[str])
- Implement parse_insights(filepath: str) -> list[InsightCard] that parses the markdown format defined in INSIGHT_FORMAT_SPEC.md
- Handle edge cases: cards without tags, multi-paragraph backs, malformed metadata (warn and skip), empty backs
- Strip leading/trailing whitespace from front and back text

Then write test_parser.py with thorough tests covering all edge cases. Include a test fixture file tests/fixtures/test_insights.md with 5-6 sample cards (use realistic life insight content, not lorem ipsum).

Run the tests and make sure they pass.
```

---

## Prompt 2: AnkiConnect client

```
Read CLAUDE.md for the AnkiConnect integration spec.

Build anki_client.py:
- Implement a simple AnkiConnect client that makes HTTP POST requests to localhost:8765
- All requests use API version 6
- Implement these methods:
  - invoke(action, **params) — generic AnkiConnect caller with error handling
  - find_notes(query: str) -> list[int] — find note IDs matching a query
  - notes_info(note_ids: list[int]) -> list[dict] — get full note details
  - add_note(deck: str, front: str, back: str, tags: list[str]) -> int — create a note
  - update_note_fields(note_id: int, front: str, back: str) -> None — update without resetting scheduling
  - replace_tags(note_id: int, tags: list[str]) -> None — sync tags on a note
- If AnkiConnect is not reachable, raise a clear error with a helpful message telling the user to start Anki
- Use Basic note type with Front/Back fields

Write test_anki_client.py with mocked HTTP responses (use unittest.mock.patch on requests.post). Test both success and error cases including connection refused.

Run the tests and make sure they pass.
```

---

## Prompt 3: Sync engine + CLI

```
Read CLAUDE.md for the sync logic and CLI spec.

Build sync.py:
- Define a SyncResult dataclass: created (int), updated (int), unchanged (int), orphaned (int), errors (list[str])
- Implement the sync logic exactly as described in CLAUDE.md:
  1. Parse markdown into InsightCards
  2. Query Anki for all notes in the target deck with insight-id:: tags
  3. Build a map of insight_id → anki_note_id
  4. For each card: create if new, update if changed, skip if identical
  5. Log orphaned cards (in Anki but not in markdown) as warnings
  6. Return SyncResult
- For tag syncing: each card gets tags from the markdown (e.g. mindset, relationships) PLUS the tracking tag insight-id::NNN
- When comparing for changes, compare both front text and back text against what's in Anki

Build the CLI entry point:
- argparse with: positional markdown_file path, --deck (default "Life Insights"), --dry-run flag, --verbose flag
- In dry-run mode, print what would happen but don't call AnkiConnect write methods
- Print a clean summary at the end: "Sync complete: 3 created, 1 updated, 12 unchanged, 0 orphaned"
- If there are errors or orphaned cards, print them clearly

Write test_sync.py testing the sync logic with mocked AnkiConnect calls. Test scenarios:
- All new cards (empty deck)
- Mix of new, changed, and unchanged cards
- Orphaned cards in Anki
- Dry run mode

Run all tests and make sure everything passes.
```

---

## After All Three Prompts

Test the full flow manually:
1. Create a sample insights.md with a few cards
2. Open Anki with AnkiConnect installed
3. Create a "Life Insights" deck in Anki
4. Run: `python -m remember.sync insights.md --verbose`
5. Verify cards appear in Anki with correct front/back/tags
6. Edit a card in the markdown, re-run, verify it updates without resetting scheduling
7. Add a new card, re-run, verify only the new one is created
