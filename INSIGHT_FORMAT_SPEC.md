# Life Insights — Format Specification

## Design Philosophy

These cards are not trivia. They exist to close the gap between **knowing** something intellectually and **living** it instinctively.

The goal of each card is to rehearse a perspective shift — so that when the real moment arrives, the skillful response fires automatically instead of the old pattern.

### How to Write a Good Insight Card

**The front is a situation or trigger.** Describe the moment where the old pattern would normally kick in. Make it vivid and specific enough that you feel a flicker of recognition when you read it.

**The back is the reframe or skillful response.** Not advice. Not a platitude. The actual shift in seeing that changes your behavior. Write it in a way that re-evokes the *felt sense* of the insight — the way it landed when you first understood it.

### Examples

Good:
- **Front:** When she's venting about her day, what am I actually being asked to do?
- **Back:** Just hold space. She's not asking me to solve it. The urge to fix is about my discomfort with her discomfort, not about helping. Presence is the gift.

Good:
- **Front:** I just got critical feedback and my chest is tight. What's actually happening?
- **Back:** The ego is conflating the work with the self. The feedback is about the artifact, not about my worth. Breathe, separate the two, and mine the feedback for signal.

Weak (too abstract, no trigger):
- **Front:** What should I remember about patience?
- **Back:** Be more patient with people.

### Why This Works

Spaced repetition + trigger-based framing = mental rehearsal. Each review is a simulated encounter with the real moment. Over weeks and months, the reframe stops being a thought you recall and becomes how you see.

---

## Technical Format

### Structure

```markdown
# Life Insights

## Card front text goes here
<!-- id: 001 | tags: mindset, relationships -->
Card back text goes here. Can be multiple lines and paragraphs.

Supports full markdown — emphasis, lists, links, whatever helps
the insight land.

## Next card front
<!-- id: 002 | tags: career -->
Back of the next card.
```

### Rules

1. **`# Life Insights`** — The H1 heading at the top of the file. Required. Only one per file.
2. **`## Card front`** — Each H2 heading starts a new card. The heading text is the card front.
3. **`<!-- id: NNN | tags: tag1, tag2 -->`** — Metadata comment, must be the first line after the H2. 
   - `id` is required. Zero-padded three-digit number (001, 002, ...). Must be unique across the file.
   - `tags` is optional. Comma-separated, drawn from the taxonomy below.
4. **Card back** — Everything after the metadata comment, up to the next `##`, is the card back.
5. **No nested headings** — Don't use `###` or deeper inside card backs. Use bold or other formatting instead.

### Tag Taxonomy

- `mindset` — mental models, cognitive reframes, emotional regulation
- `relationships` — partnership, communication, empathy, boundaries
- `career` — work habits, leadership, feedback, professional growth
- `health` — physical wellbeing, exercise, sleep, nutrition
- `music` — practice, performance, creative process
- `finance` — money decisions, investing psychology, resource allocation
- `productivity` — systems, focus, energy management, prioritization
- `pickleball` — technique, strategy, competition mindset
- `spirituality` — presence, non-dual awareness, flow, surrender
- `technical` — engineering principles, architecture, tools

---

## Sync Behavior

The sync engine compares the markdown file against the Anki deck via AnkiConnect:

| Scenario | Action |
|---|---|
| Card ID exists in markdown but not in Anki | **Create** new card in Anki |
| Card ID exists in both, content differs | **Update** card text in Anki (preserves scheduling) |
| Card ID exists in both, content identical | **Skip** (no-op) |
| Card ID exists in Anki but not in markdown | **No action** (never auto-delete) |

Cards are never deleted by the sync engine. If you remove a card from the markdown, it remains in Anki until you manually delete it. This is a safety measure to protect study data.
