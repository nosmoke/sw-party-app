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
3. Then secret rooms and secret doors — step 2b.

## 2b. Secret rooms and secret doors
The players' map is shown to the players from the start (only the areas of visited rooms), so anything
drawn on it can give a secret away: a room behind a "plain" wall, a passage stub, a door symbol.
1. **Find them in the text** while reading the adventure (plan.md): "secret door", "hidden passage",
   "concealed", "דלת סודית/סתרים", rooms reachable only through one, an "S" on the map. Put what the
   characters can find, and how (dice, who gets a bonus), in that room's `secret` field.
2. Decide for each one:
   - **A secret room** (the whole room is unknown until found) → hide it on the players' picture and
     give it a patch that shows it when the room is marked visited. Example: room 14 of "הצלת ליאם",
     a room off a corridor whose door is secret: on the players' map the corridor wall runs on unbroken
     and the room's area is plain paper; once 14 is visited the patch shows the room and its passage.
   - **A secret door between known rooms** → only the door is hidden: a wall line over it, no patch
     (or a small patch with the door, on the room behind it, if the door should appear when found).
   - The DM only marks the secret on the map with an "S" → erasing the S in step 1 (`_` key) is enough.
3. Write `work/map/secret.json` (coordinates read off zoomed map_grid pictures of the players' picture):
   ```json
   {"14": {"fills": [ {"poly": [[42.1,78.4],[46.2,78.4],[46.3,87.6],[41.6,86.0]], "like": [38,82]},
                      {"poly": [[46.3,79.0],[47.0,79.0],[47.0,87.4],[46.3,87.4]], "like": [46.6,77.5]} ],
           "walls": [ {"from": [47.35,80.6], "to": [47.35,85.4], "like": [47.35,78.5]} ]}}
   ```
   - `fills`: polygons to paint over — the room, its door/passage and its own rock or hatching — each
     with `like`, a point whose surface the area should look like (paper outside the dungeon, solid
     rock, hatching). Prefer one fill with plain paper or solid rock; textured fills (hatching) can show
     repeats, so keep those strips narrow.
   - `walls`: lines to draw where the secret door or passage met a wall that stays. `like` is a point
     on that wall a little further along it: its thickness and colour are copied and the new line is moved
     sideways onto it, so it continues the wall exactly. Make the line a bit longer than the gap.
   - `box` (optional): the patch area; default = around the fills.
4. `python3 S/map_secret.py work/map/<id>-map-players.jpg work/map/secret.json work/map/<id>-map-players.jpg work/map/secret`
   (in and out may be the same file; keep a copy of the input to redo it). Writes the patches
   (`patch-<id>.png`, cut from the picture *before* hiding, so with numbers already erased) and
   `patches.json`, and `secret_check.png`: for each room, before | hidden | hidden + patch.
5. Look at the check, then zoom on the hidden picture with map_grid: no trace of the room, its door,
   or its passage; the new wall in line with the old; the painted area blends in. Adjust and rerun from
   the saved copy. The third column must look like the first inside the orange box.
6. Pass the patches to the book: `map_json.py ... --patches work/map/secret/patches.json`.
   Also give each secret room its area in step 3 as usual — the patch shows the drawing, the area
   reveals it; both appear only when the room is marked visited.
   The DM can fine-tune patches later in the app's map editor (מדבקות).

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
