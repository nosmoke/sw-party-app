#!/usr/bin/env python3
"""Turn rough room-number positions into exact pins, and find the box of each printed number.

Usage:
  python3 map_pins.py MAP.jpg ROUGH.json OUT_DIR [--pick PICK.json] [--radius 2.5]

ROUGH.json  {"room id": [x, y], ...} percent, read off map_grid.py pictures (put the point on the
            printed number). Extra marks to erase for the players' map (secret doors "S", trap "X",
            "T") can be listed under keys starting with "_", e.g. "_s1": [x, y]; they get a box but no pin.
PICK.json   optional corrections after looking at the check sheets:
            {"12": "b"}   use candidate b instead of the default
            {"12": "-"}   keep the rough point as is, no number box (e.g. no printed number)
            {"12": [x,y]} use this exact point (and no box)
            {"12": [x0,y0,x1,y1]} use this box for the number

Writes: pins.json {"id": [x,y]} (only real rooms), labels.json {"id": [x0,y0,x1,y1]} (number boxes,
including "_" marks), pins_check_NN.png (one tile per room: blue cross = your rough point, green box =
chosen number, red letters = other candidates), pins_report.txt.
Look at every check tile. A pin is right when the green box sits exactly on that room's number.
"""
import sys, os, argparse
import cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maplib as M

ap = argparse.ArgumentParser()
ap.add_argument("map"); ap.add_argument("rough"); ap.add_argument("out")
ap.add_argument("--pick"); ap.add_argument("--radius", type=float, default=2.5)
ap.add_argument("--min-h", type=float, default=0); ap.add_argument("--max-h", type=float, default=0)
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
im = M.load(a.map); H, W = im.shape[:2]; S = min(H, W)
rough = M.jload(a.rough); pick = M.jload(a.pick) if a.pick else {}
inkm = M.ink(im)
hmin = a.min_h or max(5, S * 0.007); hmax = a.max_h or S * 0.06
R = int(a.radius / 100 * max(W, H))

pins, labels, rep, tiles = {}, {}, [], []
LET = "abcdefghijklmnopqrstuvwxyz"
STRIP = None
def candidates(x, y, lo, hi, L, long_max=None, short_max=None, ref=None):
    X0, Y0, X1, Y1 = max(0, int(x - R)), max(0, int(y - R)), min(W, int(x + R)), min(H, int(y + R))
    sub = inkm[Y0:Y1, X0:X1]; out = []
    vs = [M.strip_lines(sub, L), sub] if STRIP is None else [STRIP[Y0:Y1, X0:X1], M.strip_lines(sub, L), sub]
    for variant in vs:
        for b, sz in M.glyph_clusters(variant, lo, hi, long_max, short_max):
            bb = [b[0] + X0, b[1] + Y0, b[2] + X0, b[3] + Y0]
            if any(np.allclose(bb, c[1], atol=3) for c in out): continue
            cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2; d = ((cx - x) ** 2 + (cy - y) ** 2) ** .5
            if d <= R:
                short = min(bb[2] - bb[0], bb[3] - bb[1]); longs = max(bb[2] - bb[0], bb[3] - bb[1])
                # a printed number: short side about one digit high, long side 1-3 digits
                pen = 0 if not ref else (abs(short - ref) / ref + max(0, longs / ref - 3.2)) * R * 0.35
                out.append((d + pen, bb, sz))
    out.sort(key=lambda c: c[0]); return out
# pass 1: learn the size of the printed numbers from the nearest candidates
sizes = []
for k, p in rough.items():
    x, y = M.to_px(p, W, H); c = candidates(x, y, hmin, hmax, hmax * 1.4)
    if c and c[0][0] < R * 0.4:
        b = c[0][1]; sizes.append(min(b[2] - b[0], b[3] - b[1]) if max(b[2] - b[0], b[3] - b[1]) > 1.6 * min(b[2] - b[0], b[3] - b[1]) else c[0][2])
med = a.min_h and (a.min_h + (a.max_h or a.min_h * 1.6)) / 2 or (float(np.median(sizes)) if sizes else S * 0.02)
lo, hi = med * 0.65, med * 1.45
STRIP = M.strip_lines(inkm, med * 2.2)   # grid and wall lines are long on the whole map, digits are short
for k, p in rough.items():
    x, y = M.to_px(p, W, H)
    cands = candidates(x, y, lo * 0.5, hi, med * 1.6, med * 3.4, med * 1.5, ref=med)[:12]
    choice = 0 if cands else None
    pk = pick.get(k)
    box = None; pt = list(p)
    if isinstance(pk, str) and pk == "-": choice = None
    elif isinstance(pk, str) and pk in LET[:len(cands)]: choice = LET.index(pk)
    elif isinstance(pk, list) and len(pk) == 2: choice = None; pt = pk
    elif isinstance(pk, list) and len(pk) == 4: choice = None; box = [pk[0] / 100 * W, pk[1] / 100 * H, pk[2] / 100 * W, pk[3] / 100 * H]
    if choice is not None: box = cands[choice][1]
    if box is not None:
        pt = M.to_pct((box[0] + box[2]) / 2, (box[1] + box[3]) / 2, W, H)
        labels[k] = [round(box[0] / W * 100, 2), round(box[1] / H * 100, 2), round(box[2] / W * 100, 2), round(box[3] / H * 100, 2)]
        mv = ((pt[0] - p[0]) ** 2 + (pt[1] - p[1]) ** 2) ** .5
        if mv > 1.2 and not pk: rep.append(f"{k}: moved {mv:.1f}% from your point - check the tile")
    elif not pk: rep.append(f"{k}: no number found near your point - kept it as is")
    if not k.startswith("_"): pins[k] = pt
    # check tile
    T = 300; r2 = R * 0.9
    TX0, TY0, TX1, TY1 = max(0, int(x - r2)), max(0, int(y - r2)), min(W, int(x + r2)), min(H, int(y + r2))
    t = im[TY0:TY1, TX0:TX1].copy(); s = T / max(1, max(t.shape[:2])); t = cv2.resize(t, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
    f = lambda X, Y: (int((X - TX0) * s), int((Y - TY0) * s))
    for i, (d, bb, _sz) in enumerate(cands):
        if i == choice: continue
        cv2.rectangle(t, f(bb[0], bb[1]), f(bb[2], bb[3]), (0, 0, 220), 1)
        cv2.putText(t, LET[i], (f(bb[0], bb[1])[0], f(bb[0], bb[1])[1] - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 220), 1, cv2.LINE_AA)
    if box is not None: cv2.rectangle(t, f(box[0] - 1, box[1] - 1), f(box[2] + 1, box[3] + 1), (0, 170, 0), 2)
    # percent ruler along the top and left edge (ticks every 0.5%, labels every 1%)
    for axis in (0, 1):
        lo_, hi_ = (TX0 / W * 100, TX1 / W * 100) if axis == 0 else (TY0 / H * 100, TY1 / H * 100)
        v = np.ceil(lo_ * 2) / 2
        while v <= hi_:
            q = int(((v / 100 * (W if axis == 0 else H)) - (TX0 if axis == 0 else TY0)) * s); big = abs(v - round(v)) < 1e-6
            if axis == 0: cv2.line(t, (q, 0), (q, 9 if big else 5), (200, 60, 0), 1)
            else: cv2.line(t, (0, q), (9 if big else 5, q), (200, 60, 0), 1)
            if big: cv2.putText(t, f"{v:g}", (q + 2, 18) if axis == 0 else (11, q + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (200, 60, 0), 1, cv2.LINE_AA)
            v += 0.5
    cx, cy = f(x, y); cv2.line(t, (cx - 8, cy), (cx + 8, cy), (230, 120, 0), 2); cv2.line(t, (cx, cy - 8), (cx, cy + 8), (230, 120, 0), 2)
    t = cv2.copyMakeBorder(t, 24, max(0, T - t.shape[0]), 0, max(0, T - t.shape[1]), cv2.BORDER_CONSTANT, value=(255, 255, 255))
    lab = k[::-1] if any('֐' <= ch <= '׿' for ch in k) else k
    cv2.putText(t, f"room {lab}", (4, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.rectangle(t, (0, 0), (t.shape[1] - 1, t.shape[0] - 1), (180, 180, 180), 1)
    tiles.append(t)
cols = 5
for s0 in range(0, len(tiles), cols * 4):
    ch = tiles[s0:s0 + cols * 4]
    while len(ch) % cols: ch.append(np.full_like(tiles[0], 255))
    cv2.imwrite(os.path.join(a.out, f"pins_check_{s0 // (cols*4) + 1:02d}.png"), np.vstack([np.hstack(ch[i:i + cols]) for i in range(0, len(ch), cols)]))
M.jsave(pins, os.path.join(a.out, "pins.json")); M.jsave(labels, os.path.join(a.out, "labels.json"))
open(os.path.join(a.out, "pins_report.txt"), "w").write("\n".join(rep) + "\n")
print(f"{len(pins)} pins, {len(labels)} number boxes (number height about {med:.0f}px)." + ("\n" + "\n".join(rep) if rep else ""))
