#!/usr/bin/env python3
"""Assemble the book's "map" section from the map work folder.

  python3 map_json.py BOOK_ID WORK_MAP_DIR OUT_DIR [--page "עמ' 6"] [--note "..."] [--players-note "..."] [--patches patches.json]

Reads WORK_MAP_DIR/dm.jpg, <id>-map-players.jpg (or players.jpg), pins.json, regions.json;
copies the pictures into OUT_DIR as <id>-map.jpg / <id>-map-players.jpg (+ patch pictures) and writes
OUT_DIR/map.json, ready for book["map"] (build_book.py: "map": json.load(open(".../map.json"))).
"""
import sys, os, json, shutil, argparse
ap = argparse.ArgumentParser(); ap.add_argument("id"); ap.add_argument("work"); ap.add_argument("out")
ap.add_argument("--page", default=""); ap.add_argument("--note", default=""); ap.add_argument("--players-note", default="עותק לשחקנים: מספרי החדרים וסימוני המנחה נמחקו.")
ap.add_argument("--patches"); ap.add_argument("--dm", default="dm.jpg")
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
J = lambda f: json.load(open(os.path.join(a.work, f), encoding="utf-8")) if os.path.exists(os.path.join(a.work, f)) else None
dm = os.path.join(a.work, a.dm)
ext = os.path.splitext(dm)[1].lower() or ".jpg"
shutil.copy(dm, os.path.join(a.out, f"{a.id}-map{ext}"))
m = {"file": f"books/{a.id}-map{ext}"}
if a.page: m["page"] = a.page
if a.note: m["note"] = a.note
pins = J("pins.json")
if pins: m["pins"] = pins
pl = next((p for p in (os.path.join(a.work, f"{a.id}-map-players.jpg"), os.path.join(a.work, "players.jpg")) if os.path.exists(p)), None)
if pl:
    shutil.copy(pl, os.path.join(a.out, f"{a.id}-map-players.jpg"))
    m["players"] = {"file": f"books/{a.id}-map-players.jpg", "note": a.players_note}
    rg = J("regions.json")
    if rg: m["players"]["regions"] = rg
    if a.patches:
        pt = json.load(open(a.patches, encoding="utf-8")); out = []
        for x in pt:
            f = x["file"]; name = f"{a.id}-room{x['room']}{os.path.splitext(f)[1]}"
            shutil.copy(f, os.path.join(a.out, name)); out.append({"room": str(x["room"]), "box": x["box"], "file": f"books/{name}"})
        m["players"]["patches"] = out
json.dump(m, open(os.path.join(a.out, "map.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(os.path.join(a.out, "map.json"), "| pins", len(m.get("pins", {})), "| regions", len(m.get("players", {}).get("regions", {})))
