# Maps: pins, players' map and room areas

Goal (what the app does with it): the DM sees the full map with a pin on every room; the players see
`map.players.file` (no numbers, no DM marks), but only the areas (`regions`) of rooms marked visited or
cleared. So the quality bar is: every pin exactly on its room number, every room's area covering that
room's floor (and the corridor bits that belong to it) and nothing of its neighbours, and a players'
picture with no numbers or secrets left.

`S` below = `${CLAUDE_SKILL_DIR}/scripts` (the scripts folder of this skill). Work in a folder such as
`work/map/`. All coordinates are percent of the picture (0–100) from the top-left corner.

**You read the map; the scripts measure.** Never guess positions from the small overview: always read
them off a grid picture, then let the scripts snap them to the ink, then look at the check pictures.

## 0. The picture
- From a PDF: look at `images/` from extract.py first (embedded original, best quality). Otherwise crop
  the page picture: `python3 S/map_prep.py crop pages/p006.png work/map/dm.jpg 8 12 94 88`
  (read the box off `map_grid.py pages/p006.png work/map/page` first).
- Turn it upright if the text on the map is sideways (`--rotate 90`). Numbers written sideways are fine
  if that is how the map is printed.
- Several levels on separate pages → `map_prep.py join` into one picture (the app has one map per book).
- `map_prep.py fit` to 1400–2400 px on the long side. Do all of this **before** placing pins: pins and
  areas are tied to this exact picture; the same picture (same size) is used for the players' copy.
- Name the files `<book-id>-map.jpg` and `<book-id>-map-players.jpg`.

## 1. Pins
1. `python3 S/map_grid.py work/map/dm.jpg work/map/g` → `grid_all.png`, then zoomed tiles:
   `--tiles 3x2` (more tiles for big or crowded maps; every room number must be clearly legible in a tile).
2. Go tile by tile. For every room number write its centre in `work/map/rough.json`:
   `{"1": [9.3, 15.6], "2": [14.7, 10.3], ...}` — read x on the top ruler and y on the left ruler,
   to about 0.3%. Use the room ids of the book (`"5א"`, `"12b"` as printed).
   Also add every DM-only mark the players must not see, under keys starting with `_`: secret-door "S",
   trap "X"/"T", arrows with notes, "start here" — `"_s1": [40.1, 52.3]`.
   A room whose number appears twice: give the second as `"_2b"` (erased, no pin).
   A room with no printed number: put its pin in the middle of the room and later pick `"-"`.
3. `python3 S/map_pins.py work/map/dm.jpg work/map/rough.json work/map`
   → `pins_check_NN.png`: for each room a zoomed tile, blue cross = your point, **green box = the
   chosen number**, red letters = other candidates.
4. Look at **every** tile. Wrong pick → `work/map/pick.json`: `{"12": "c"}` (that candidate),
   `{"7": [x0,y0,x1,y1]}` (exact box), `{"9": "-"}` (no box, keep point), `{"9": [x, y]}` (exact point).
   Re-run with `--pick work/map/pick.json` until every green box sits on its own number and nothing else.
   Note the warnings in `pins_report.txt` (moved far / nothing found).
   Result: `pins.json` (→ `map.pins`) and `labels.json` (number boxes, used in steps 2 and 3).

## 2. The players' map
1. `python3 S/map_players.py work/map/dm.jpg work/map/labels.json work/map/<id>-map-players.jpg [--extra extra.json]`
   `extra.json` = more boxes to erase `[[x0,y0,x1,y1], ...]`: a DM legend, the title "מפת המנחה",
   room numbers inside a legend. `{"box": [...], "fill": true}` paints a whole box with the colour around it.
2. Look at `..._check.png` (before/after of each box) **and** at the whole players' picture zoomed with
   map_grid. Nothing numbered or secret may remain. Floor grid lines under a number may fade — fine.
3. Secret doors drawn as a door symbol in a wall cannot be erased cleanly by inpainting. Options, in order:
   leave the symbol and write in `map.players.note` that the secret doors are drawn; or, if the room
   behind it is secret, that is already safe (its area shows only when visited). Do not hand-paint.
4. A room that should *look different* once found (a secret room hidden behind a plain wall on the
   players' picture) uses `players.patches`: `{"room": "8", "box": [x0,y0,x1,y1], "file": "books/<id>-room8.png"}`
   — a crop of the DM picture shown over the players' picture when room 8 is visited.
   Make it with `map_prep.py crop dm.jpg room8.png x0 y0 x1 y1` from the *DM* picture after erasing
   numbers (run map_players on it first if needed).

## 3. Room areas (regions)
Every floor area should belong to some room, or the players will never see it. Corridors: give a
corridor to the room whose text describes it; otherwise split it between the rooms at its ends (or to the
lower-numbered room). Stairs/doors between rooms: to either side, not both.

1. Write `work/map/rooms_rough.json`, reading coordinates off grid tiles (same rules as pins):
   - rectangular room → `"4": [[x0, y0, x1, y1]]` — put each edge on the *middle of the wall line*;
     the script snaps each edge to the nearest wall within 1.2%.
   - room + alcove/corridor, L-shape → several rectangles: `"6": [[...], [...]]`
   - cave, round or irregular room → `"7": "flood"` (fills the floor around the pin up to the walls;
     neighbouring flood rooms are split at their narrowest point). If it leaks through a doorway, use
     `{"flood": true, "door": 12}` (closes gaps up to 12 px) and/or `"clip": [x0,y0,x1,y1]` (stay inside).
   - anything else → a polygon `"9": [[[x,y], [x,y], ...]]`, clockwise, 4–16 points, on the wall middles.
   - no area (a room off the map, a feature that is not a place) → `"11": []`.
   Rectangles are given first; floods never spill into an area already given to a rectangle/polygon,
   so give the easy rooms as rectangles and flood only what is left.
2. `python3 S/map_rooms.py work/map/dm.jpg work/map/pins.json work/map/rooms_rough.json work/map --labels work/map/labels.json`
   → `regions.json`, `rooms_preview.png`, `rooms_report.txt`.
3. Check: read the report (pin outside its area, big overlaps, leaks, rooms without area), and look at
   `rooms_preview.png` and at zoomed grids with the areas drawn:
   `python3 S/map_grid.py work/map/dm.jpg work/map/g --tiles 3x2 --overlay work/map/regions.json --overlay work/map/pins.json`
   Every room coloured, colour stops at the walls, no colour on rock/outside, neighbours do not overlap,
   doors and corridor pieces assigned once. Fix the rough file and re-run until clean.
   Typical fixes: a snapped edge jumped to the wrong wall → make the rectangle more exact or add
   `"!4": "nosnap"`; a flood leaked → bigger `door`, a `clip`, or a polygon.
4. `regions.json` → `map.players.regions`.

## 4. Put it in the book
```json
"map": {
  "file": "books/<id>-map.jpg", "page": "עמ' 6", "note": "מפה: <cartographer> (עמ' 1).",
  "pins": { …pins.json… },
  "players": { "file": "books/<id>-map-players.jpg",
               "note": "עותק לשחקנים: מספרי החדרים וסימוני המנחה נמחקו.",
               "regions": { …regions.json… } }
}
```
Image paths always start with `books/` and use the bare file names; bundle.py finds the files by name.
If the source has no map, leave `map` out (the app works without one) and say so to the user.
Without `regions` the players' map stays dark for the whole adventure (the app reveals only the areas
of visited rooms), so finish the areas; if some room truly cannot get one, give it none and tell the user.
