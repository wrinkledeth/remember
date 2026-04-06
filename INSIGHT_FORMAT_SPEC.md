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

<!-- Section: Relationships -->

## When she's venting about her day
<!-- id: a3f8b2c1 -->
and I feel the urge to jump in with solutions
---
Just hold space. She's not asking me to solve it.
The urge to fix is about my discomfort with her discomfort.

## I just got critical feedback and my chest is tight.
---
The ego is conflating the work with the self.
The feedback is about the artifact, not about my worth.
```

### Rules

1. **`# Title`** — The H1 heading at the top of the file. Ignored by the parser.
2. **`## Card front`** — Each `##` heading starts a new card. The heading text is the first line of the front.
3. **`---`** — Horizontal rule separates front from back. **Required** for every card. Everything between `##` and `---` is the front (multi-line supported). Everything after `---` until the next `##` is the back.
4. **`<!-- id: NNN -->`** — ID comment. Optional. If omitted, `remember sync` auto-generates an 8-char hex ID and writes it into the file after the `##` heading. If present, it must appear between `##` and `---`. It is excluded from front text. IDs must be unique across the file.
5. **Comments and non-card content** — HTML comments (`<!-- ... -->`), prose, and blank lines outside of card blocks are ignored by the parser. Use them freely for sections, notes, or TODOs.
6. **No nested headings** — Don't use `###` or deeper inside card fronts or backs. Use bold or other formatting instead.
7. **Filename = deck name** — The markdown filename determines the Anki deck. `relationships.md` syncs to deck "Relationships".

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
