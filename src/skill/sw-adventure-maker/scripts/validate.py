#!/usr/bin/env python3
"""Check a book the way the app's import does, plus extra checks for things the app accepts but
that would play badly. Usage:  python3 validate.py BOOK.json [IMAGES_DIR]   (or a packed .sw-adventure.json)
Exit code 1 when there are errors (the app would refuse the file)."""
import sys, os, re, json
p = sys.argv[1]; imgdir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(p))
o = json.load(open(p, encoding="utf-8"))
entries = [(e["book"], e.get("images", {})) for e in o["books"]] if isinstance(o, dict) and "books" in o else [(o, None)]
DICE = re.compile(r"^\s*(\d*)ק(\d+)\s*([+\-−]\s*\d+)?\s*$")
def has_img(ref, imgs):
    if imgs is not None: return ref in imgs
    return os.path.exists(os.path.join(imgdir, os.path.basename(ref)))
bad = 0
for b, imgs in entries:
    er, wn = [], []
    bid = str(b.get("id", "")).strip()
    if not bid: er.append("no id")
    elif not re.match(r"^[a-z0-9][a-z0-9-]{1,40}$", bid): er.append(f"id '{bid}' invalid: lowercase English letters, digits and '-' only, 2-41 chars")
    if not b.get("title"): er.append("no title")
    rooms = b.get("rooms") or []
    if not rooms: er.append("no rooms")
    R, F = set(), {f.get("id") for f in b.get("flags", []) if f.get("id")}
    for i, r in enumerate(rooms):
        rid = str(r.get("id", "")).strip()
        if not rid: er.append(f"room #{i+1} has no id"); continue
        if rid in R: er.append(f"room id {rid} appears twice")
        R.add(rid)
        if not r.get("name"): wn.append(f"room {rid} has no name")
        if not (r.get("read") or r.get("dm")): wn.append(f"room {rid} has neither read-aloud text nor DM notes")
        if not r.get("page"): wn.append(f"room {rid} has no page")
    for r in rooms:
        rid = str(r.get("id"))
        for m in r.get("monsters", []):
            if not m.get("name"): er.append(f"room {rid}: a monster without a name"); continue
            for f in ("ac", "count", "save", "xp"):
                if f in m and not isinstance(m[f], (int, float)): wn.append(f"room {rid} '{m['name']}': {f} should be a number, got {m[f]!r}")
            if m.get("ac") is None: wn.append(f"room {rid} '{m['name']}': no AC (ac)")
            if m.get("hd") is None and m.get("hp") is None: wn.append(f"room {rid} '{m['name']}': no hd or hp")
            if isinstance(m.get("ac"), (int, float)) and m["ac"] < 9: wn.append(f"room {rid} '{m['name']}': ac {m['ac']} looks like descending AC - the Hebrew books use ascending (19 - descending)")
        for t in r.get("traps", []):
            if t.get("dmg") and not DICE.match(str(t["dmg"]).replace("d", "ק")): wn.append(f"room {rid} trap '{t.get('name')}': dmg '{t['dmg']}' is not a dice roll like 2ק6+1")
            if "ק" not in str(t.get("dmg", "ק")) and "d" in str(t.get("dmg", "")): wn.append(f"room {rid} trap: write dice with ק (1ק6), not d")
        for t in r.get("treasure", []):
            if "gp" in t and not isinstance(t["gp"], (int, float)): wn.append(f"room {rid} treasure '{t.get('name')}': gp must be a number")
        for x in r.get("events", []):
            if x.get("fight") and str(x["fight"].get("from")) not in R: wn.append(f"room {rid}: event fight from room {x['fight'].get('from')} which does not exist")
            if x.get("flag") and x["flag"] not in F: wn.append(f"room {rid}: event flag '{x['flag']}' not in book flags")
        for k in (r.get("flagNotes") or {}):
            if k not in F: wn.append(f"room {rid}: flagNotes '{k}' not in book flags")
        for ad in r.get("adjust", []):
            if ad.get("op") != "noevent" and not any(m.get("name") == ad.get("mon") for m in r.get("monsters", [])): wn.append(f"room {rid}: adjust refers to '{ad.get('mon')}', not in the room")
    for g in b.get("goals", []):
        if not g.get("id") or not g.get("name") or not isinstance(g.get("xp"), (int, float)): wn.append(f"goal {g.get('name') or g.get('id')}: needs id, name and numeric xp")
    M = b.get("map")
    if not M: wn.append("no map")
    else:
        if M.get("file") and not has_img(M["file"], imgs): wn.append(f"DM map image missing: {M['file']}")
        pins = M.get("pins", {})
        for k, v in pins.items():
            if k not in R: wn.append(f"pin for unknown room {k}")
            if not (isinstance(v, list) and len(v) == 2 and all(isinstance(q, (int, float)) and 0 <= q <= 100 for q in v)): er.append(f"pin {k} must be [x, y] in percent 0-100")
        nop = [k for k in R if k not in pins]
        if pins and nop: wn.append(f"rooms without a pin: {', '.join(nop)}")
        P = M.get("players")
        if not P: wn.append("no players' map")
        else:
            if not P.get("file") or not has_img(P["file"], imgs): wn.append(f"players' map image missing: {P.get('file')}")
            rg = P.get("regions", {})
            for k, polys in rg.items():
                if k not in R: wn.append(f"region for unknown room {k}")
                for poly in polys:
                    if len(poly) < 3 or not all(isinstance(pt, list) and len(pt) == 2 and 0 <= pt[0] <= 100 and 0 <= pt[1] <= 100 for pt in poly): er.append(f"region {k}: each polygon needs 3+ [x,y] points in 0-100")
            nor = [k for k in R if k not in rg]
            if rg and nor: wn.append(f"rooms the players will never see on the map (no region): {', '.join(nor)}")
            for x in P.get("patches", []):
                if not has_img(x.get("file", ""), imgs): wn.append(f"patch image missing: {x.get('file')}")
    n_m = sum(int(m.get("count", 1) or 1) for r in rooms for m in r.get("monsters", []))
    print(f"== {bid or '?'}: {b.get('title','')} | rooms {len(rooms)} | monsters {n_m} | traps {sum(len(r.get('traps',[])) for r in rooms)} | treasure {sum(len(r.get('treasure',[])) for r in rooms)}"
          + (f" | pins {len(M.get('pins',{}))} | regions {len((M.get('players') or {}).get('regions',{}))}" if M else ""))
    for e in er: print("  ERROR  ", e)
    for w in wn: print("  warning", w)
    if not er and not wn: print("  ok")
    bad += len(er)
sys.exit(1 if bad else 0)
