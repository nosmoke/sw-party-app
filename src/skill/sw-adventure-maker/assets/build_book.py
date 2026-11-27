#!/usr/bin/env python3
"""Template: write the book as Python, so long Hebrew texts stay readable and helpers fill the
repetitive parts. Copy to work/build_book.py, fill in, run:  python3 work/build_book.py work/<id>.json
Keep each room's text close to the source; every note ends with its page "(עמ' N)"."""
import json, sys

ID = "my-adventure"                       # lowercase English letters, digits, "-"
P = lambda n: f"עמ' {n}"                   # page label

# ---- monsters used more than once: one helper per kind (stats from the adventure; monsters.md for names)
def goblin(n=1, extra=""):
    return {"name": "גובלין", "count": n, "hd": "1ק6", "ac": 12, "atk": "נשק (1ק6)", "save": 18, "move": 9, "xp": 10,
            "special": "−1 להתקפה באור יום." + (" " + extra if extra else "")}

def room(id, name, page, read=None, dm=(), **kw):
    r = {"id": str(id), "name": name, "page": P(page)}
    if read: r["read"] = read
    if dm: r["dm"] = list(dm)
    for k in ("secret", "exits", "monsters", "traps", "treasure", "events", "adjust", "tables", "flagNotes"):
        if kw.get(k): r[k] = kw[k]
    return r

rooms = [
    room(1, "הכניסה", 4,
         read="…מה שהדמויות רואות…",
         dm=["…מה קורה כשנכנסים… (עמ' 4)", "…פרט נוסף… (עמ' 4)"],
         monsters=[goblin(3)],
         traps=[{"name": "בור מכוסה", "text": "… הצלה נגד מלכודות וסכנות, כישלון: נופלים (עמ' 4).", "dmg": "1ק6", "xp": 30, "hits": {"first": 1, "half": False}}],
         treasure=[{"name": "20 מטבעות זהב", "text": "בכיס של המנהיג.", "gp": 20},
                   {"name": "3 לפידים", "ref": "torch", "qty": 3}],
         exits="צפונה ← 2. מזרחה ← 3."),
]

book = {
    "id": ID,
    "title": "שם ההרפתקה",
    "source": "שם החוברת, עמ' 1–20",          # + author / translation credit
    "levels": "דרגות 1–3 · 4–6 דמויות",
    "summary": "…תקציר למנחה, 2–4 משפטים…",
    # "readNote": "קטעי ההקראה כאן הם תמצית שלי…",   # only if the read-aloud texts are not the source's own
    "intro": {"page": P(3), "read": "…פתיחה להקראה…", "dm": ["…איך מתחילים… (עמ' 3)"]},
    "goals": [],                                # [{"id":"save_liam","name":"…","xp":250,"perChar":False,"page":P(19)}]
    "flags": [],                                # [{"id":"alarm","name":"האזעקה הופעלה","page":P(7)}]
    "after": "…מה קורה בסוף, נק״ן לסיום… (עמ' 20)",
    "rooms": rooms,
    # "map": json.load(open("work/map/map.json")),   # built in the map steps (references/maps.md)
}
json.dump(book, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(rooms), "rooms ->", sys.argv[1])
