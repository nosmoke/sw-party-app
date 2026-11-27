---
name: sw-adventure-maker
description: Turn a Swords & Wizardry (חרבות וכשפים) adventure - a PDF, page photos or scans, or the user's own Word/text document, in Hebrew or English - into a Hebrew adventure file for the party app (אפליקציית החבורה), with rooms, monsters, traps, treasure, a DM map with pins and a players' map with room areas. Use when the user wants to prepare, convert, scan, translate or upload an adventure for the app.
---

# Adventure → party-app file

You produce **one file**, `<id>.sw-adventure.json`, that the user imports in the party app:
הגדרות ← ספרייה ← העלאת הרפתקה. The app shows a check before saving. Everything the DM and the
players read is **Hebrew**; an English source is translated.

`S` = `${CLAUDE_SKILL_DIR}/scripts` — the `scripts` folder next to this SKILL.md (if the variable is
empty, find the folder that contains this file). Scripts need Python 3 with opencv, numpy, scipy,
scikit-image and Pillow (`pip install opencv-python-headless scikit-image pillow` if one is missing).
Work in `work/`; final files in `work/out/`.

References (open each at the step that needs it):
- `references/format.md` — every field of the book. Read it fully before writing the book.
- `references/hebrew-style.md` — Hebrew game terms, AC/feet/coins conversions, writing rules.
- `references/monsters.md` — Hebrew monster names and stats from the Hebrew DM handbook.
- `references/items.md` — shop item ids (`ref`) for ordinary treasure items.
- `references/maps.md` — the map procedure (pins, players' map, room areas). Follow it step by step.
- `assets/build_book.py` — template for writing the book.

## 1. Take in the source
1. `python3 S/extract.py <files...> work/src` — page pictures in `pages/`, text in `text/`, embedded
   pictures in `images/`, and `summary.txt`. Photos/scans have no text: read the page pictures.
2. Read the **whole** adventure before writing anything (pictures for layout: boxed read-aloud text,
   tables, stat blocks, sidebars; the text layer can scramble columns — check it against the picture).
3. Make `work/plan.md`: title; source and credits (author, cartographer, licence); levels and party size;
   the list of keyed areas `id – name – page`; the maps (which page, one or several levels);
   names of people/places with their Hebrew spelling; every monster kind with its Hebrew name
   (monsters.md) and stats; story events that change later rooms (→ `flags`) and achievements that give
   XP (→ `goals`); wandering-monster and other tables; anything unclear.
4. Ask the user only what you cannot decide well yourself, in one short message, and continue with
   your defaults if there is no answer: the book `id` (default: short English slug of the title),
   whether to keep the source's room numbers (default yes; they must never change later), and for an
   English source any names they want spelled a certain way. Never ask about things the file decides.

## 2. Write the book
Copy `assets/build_book.py` to `work/build_book.py` and fill it (Python keeps the long Hebrew readable,
helpers avoid repeating stat blocks). Write rooms in batches of ~8 and run it after each batch.
Rules:
- One entry per keyed area of the source, ids exactly as printed ("12", "5א", "B3"). Unkeyed but
  important places may get an id like "12a" only if the user agrees.
- `read` = the source's boxed/read-aloud text, translated. No boxed text → a short summary of what the
  characters perceive, and a book-level `readNote` saying so.
- `dm` = the rest of the key, as separate notes, each ending with "(עמ' N)". Keep every number.
- Monsters as fields (`name`, `count`, `hd`, `ac` ascending, `atk`, `save`, `move`, `xp`, `special`),
  one entry per kind per room. Hidden/optional monsters still go in the room where they fight.
  Monsters that come from elsewhere when an alarm sounds → `events` with `fight.from`.
- Traps with `dmg` as dice ("2ק6"), `hits`, `xp` if the source gives trap XP.
- Treasure: coins with numeric `gp` (silver = 0.1 gp); ordinary gear with `ref` from items.md;
  magic and special items `item: true` with their full description in `text`.
- `adjust` only when the source tells how to scale encounters to party size/level.
- `tables` for random tables (wandering monsters, fountains…), in the room where they are used.
- Book level: `title`, `source` (with page range and credits), `levels`, `summary`, `intro`, `goals`,
  `flags`, `after` (ending, XP awards).
- Translation: faithful, not adapted (hebrew-style.md). Your own interpretation goes in a separate note
  marked "(פרשנות שלי: …)". Never invent content to fill gaps.

## 3. The map
Follow `references/maps.md`: prepare the picture, pins (`map_grid.py` → `map_pins.py` with checking),
players' picture (`map_players.py`), room areas (`map_rooms.py` with checking), then `map_json.py`
and put `"map": json.load(open("work/out/map.json"))` in the book. This is the part users notice most:
take the time to look at every check picture and fix what is off. Typical effort: one rough pass plus
one or two correction passes per step.

## 4. Check and pack
1. `python3 work/build_book.py work/out/<id>.json`
2. `python3 S/validate.py work/out/<id>.json work/out` — fix every ERROR, read every warning
   (rooms without pins/areas, AC that looks descending, dice not in ק form…).
3. Read through the finished JSON once as the DM would: room by room against the source pages —
   nothing missing (a monster, a trap, a secret door, a treasure item), numbers right, Hebrew natural.
4. `python3 S/bundle.py work/out/<id>.sw-adventure.json work/out/<id>.json --images work/out`
5. Give the user the `.sw-adventure.json` file (one file, pictures inside) and, in Hebrew, 3–6 lines:
   how to import it (הגדרות ← ספרייה ← העלאת הרפתקה, בחירת הקובץ, בדיקה ושמירה), what is in it
   (rooms/monsters/pins/areas), and an honest list of what you were unsure of or could not do
   (unclear pages, interpretations, map parts to fine-tune in the app later).

## Updating a book that is already in the app
Ask the user to download it from the app (ספרייה ← הורדה) and give you that file; change it (never
the room ids — saved games refer to them); bundle again with the same `id`. Importing a file with the
same `id` replaces the book.

## Rights
The user converts adventures they own or wrote, for their own group. Keep the source credits in
`source` and, for licensed works (e.g. CC BY-NC-SA), the licence. Do not add content from other
books than the one given.
