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
To run from anywhere, add the following alias:

```bash
alias remember="uv run --project /path/to/remember remember"
```

Create a `remember.toml` in your project root:

```toml
cards_dir = "./cards" 
```


Directory structure at cards_dir mirrors Anki's deck hierarchy:

```
cards/
  all/
    tech/
      ableton.md            → All::Tech::Ableton
      anki.md               → All::Tech::Anki
```

## Usage

In this example, I pull from `All::Tech::*` into markdown, make some edits in my markdown files, and then push back into anki.

### Pull

Import an existing Anki deck into markdown. Recurses into subdecks, creating one file per deck (along with any folders).


```bash
remember pull All::Tech  

  Wrote 65 card(s) to cards/all/tech/ableton.md
  Wrote 10 card(s) to cards/all/tech/anki.md
```

### Status

Check what would change without syncing.

```bash
remember status --verbose

All::Misc (all/misc.md): 12 synced
  [changed] dc12432f: show comping (all takes)
All::Tech::Ableton (all/tech/ableton.md): 1 changed, 1 unstamped, 64 synced
All::Tech::Anki (all/tech/anki.md): 10 synced
```

### Push

Sync markdown cards to Anki. Creates new cards, updates changed ones, preserves scheduling.


```bash
remember push            

--- all/tech/ableton.md → All::Tech::Ableton ---
1 card(s) stamped with new IDs
1 created, 1 updated, 0 pulled, 64 unchanged, 0 orphaned, 0 deleted, 1 stamped

--- all/tech/anki.md → All::Tech::Anki ---
0 created, 0 updated, 0 pulled, 10 unchanged, 0 orphaned, 0 deleted, 0 stamped
```
If a card was edited in both places and Anki's version is newer, you'll get an interactive prompt:

- **`m`** — keep **m**arkdown (push to Anki)
- **`a`** — keep **a**nki (pull into markdown)
- **`s`** — **s**kip

Cards removed from markdown are flagged as orphans — you'll be prompted before anything is deleted from Anki.

##  Card format
`##` starts a card. `---` separates front from back. Everything else is ignored. Fronts and backs can be multiple lines.

IDs are auto-generated on first sync and written back into the file as `<!-- id: xxxxxxxx -->` comments. You never need to manage them.

Examples: 
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

## Limitations

- Only supports notes with Front/Back fields (Basic and similar). Cloze, image occlusion, etc. are not supported.
- Cards with media (`<img>`, `[sound:]`) are skipped during pull.
