#!/usr/bin/env python3
"""Build the room areas for the players' map from rough shapes, fitted to the drawn walls.

Usage:
  python3 map_rooms.py MAP.jpg PINS.json ROUGH.json OUT_DIR [--labels LABELS.json] [--dark 110] [--door 6]

ROUGH.json, one entry per room (percent coordinates, read off map_grid.py pictures):
  "3":  [[x0, y0, x1, y1]]                 a rectangle; its edges snap to the nearest wall line
  "3":  [[x0,y0,x1,y1], [x0,y0,x1,y1]]     several rectangles (an L-shaped room, room + alcove)
  "3":  [[[x,y], [x,y], [x,y], ...]]       a polygon, used exactly as given (no snapping)
  "3":  "flood"                            fill the floor around the pin up to the walls (caves,
                                           round rooms). Doorways wider than --door px leak: then
                                           give the room a polygon, or {"flood": true, "door": 12}
  "3":  {"flood": true, "door": 12, "clip": [x0,y0,x1,y1]}   flood with a bigger door size,
                                           and/or kept inside a box
  "3":  [[x0,y0,x1,y1]], "!3": "nosnap"   (any key "!id" = "nosnap": keep that room's rectangles as given)
Rectangles and polygons may be mixed in one list.

Writes: regions.json (ready for map.players.regions), rooms_preview.png (all areas coloured, with
ids), rooms_report.txt (leaks, rooms without an area, pins outside their own area, big overlaps).
"""
import sys, os, argparse, colorsys
import cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maplib as M

ap = argparse.ArgumentParser()
ap.add_argument("map"); ap.add_argument("pins"); ap.add_argument("rough"); ap.add_argument("out")
ap.add_argument("--labels"); ap.add_argument("--dark", type=int, default=110, help="ink darker than this is a wall (0-255)")
ap.add_argument("--door", type=int, default=6, help="flood: gaps narrower than this (px) are closed")
ap.add_argument("--snap", type=float, default=1.2, help="how far (percent) a rectangle edge may move to meet a wall")
ap.add_argument("--max-area", type=float, default=15, help="flood: give up when the area passes this percent of the map")
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
im = M.load(a.map); H, W = im.shape[:2]; S = min(H, W)
pins = M.jload(a.pins); rough = M.jload(a.rough); labels = M.jload(a.labels) if a.labels else {}
g = M.gray_norm(im)
dark = (g < a.dark).astype(np.uint8)
for b in labels.values():
    x0, y0, x1, y1 = int(b[0] / 100 * W) - 1, int(b[1] / 100 * H) - 1, int(b[2] / 100 * W) + 2, int(b[3] / 100 * H) + 2
    dark[max(0, y0):y1, max(0, x0):x1] = 0
rep = []
P = lambda x, y: [round(x / W * 100, 2), round(y / H * 100, 2)]

def snap_rect(r):
    x0, y0, x1, y1 = r[0] / 100 * W, r[1] / 100 * H, r[2] / 100 * W, r[3] / 100 * H
    t = a.snap / 100 * max(W, H)
    def best_col(xc, ya, yb):
        ya, yb = int(ya + (yb - ya) * .1), int(yb - (yb - ya) * .1)
        lo, hi = max(0, int(xc - t)), min(W - 1, int(xc + t))
        if yb <= ya or hi <= lo: return xc
        prof = dark[ya:yb, lo:hi + 1].sum(axis=0).astype(float)
        if prof.max() < 0.35 * (yb - ya): return xc
        cols = np.nonzero(prof >= 0.8 * prof.max())[0] + lo
        return float(cols[np.argmin(abs(cols - xc))])
    def best_row(yc, xa, xb):
        xa, xb = int(xa + (xb - xa) * .1), int(xb - (xb - xa) * .1)
        lo, hi = max(0, int(yc - t)), min(H - 1, int(yc + t))
        if xb <= xa or hi <= lo: return yc
        prof = dark[lo:hi + 1, xa:xb].sum(axis=1).astype(float)
        if prof.max() < 0.35 * (xb - xa): return yc
        rows = np.nonzero(prof >= 0.8 * prof.max())[0] + lo
        return float(rows[np.argmin(abs(rows - yc))])
    nx0, nx1 = best_col(x0, y0, y1), best_col(x1, y0, y1)
    ny0, ny1 = best_row(y0, x0, x1), best_row(y1, x0, x1)
    if nx1 - nx0 < 4 or ny1 - ny0 < 4: return r
    return [round(nx0 / W * 100, 2), round(ny0 / H * 100, 2), round(nx1 / W * 100, 2), round(ny1 / H * 100, 2)]

def rect_poly(r): return [[r[0], r[1]], [r[2], r[1]], [r[2], r[3]], [r[0], r[3]]]

def seed_of(k, bar):
    x, y = [int(v) for v in M.to_px(pins[k], W, H)]
    r = int(S * 0.04); X0, Y0 = max(0, x - r), max(0, y - r)
    ys, xs = np.nonzero(bar[Y0:y + r, X0:x + r] == 0)
    if not len(xs): return None
    j = np.argmin((xs + X0 - x) ** 2 + (ys + Y0 - y) ** 2)
    return int(xs[j] + X0), int(ys[j] + Y0)

def to_polys(reg):
    cs, _ = cv2.findContours(reg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = []
    for c in sorted(cs, key=cv2.contourArea, reverse=True):
        if cv2.contourArea(c) < 0.05 * reg.sum(): continue
        p = cv2.approxPolyDP(c, 0.003 * max(W, H), True).reshape(-1, 2)
        if len(p) >= 3: out.append([P(float(px), float(py)) for px, py in p])
    return out

def floods(items, taken):
    """items: {id: (door, clip)}. Rooms whose floods join are split between their pins at the
    narrowest place (watershed on the distance to the walls)."""
    from scipy import ndimage as ndi
    from skimage.segmentation import watershed
    out = {}; groups = {}
    for k, (door, clip) in items.items():
        sd = None
        if k not in pins: rep.append(f"{k}: flood needs a pin"); continue
        reg = None; tried = []
        for dd in ([door] if explicit.get(k) else sorted({door, 10, 14, 20, 28})):
            if dd < door: continue
            bar = cv2.dilate(dark, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(1, dd), max(1, dd))))
            bar = np.maximum(bar, taken)
            if clip:
                cx0, cy0, cx1, cy1 = int(clip[0] / 100 * W), int(clip[1] / 100 * H), int(clip[2] / 100 * W), int(clip[3] / 100 * H)
                m = np.ones_like(bar); m[max(0, cy0):cy1, max(0, cx0):cx1] = 0; bar = np.maximum(bar, m)
            sd = seed_of(k, bar)
            if not sd: break
            ff = bar.copy() * 255; mask = np.zeros((H + 2, W + 2), np.uint8)
            cv2.floodFill(ff, mask, sd, 128)
            r_ = (ff == 128).astype(np.uint8); area = r_.sum() / float(W * H) * 100
            leaked = area > a.max_area or r_[0].any() or r_[-1].any() or r_[:, 0].any() or r_[:, -1].any()
            tried.append((dd, area, r_))
            if not leaked: reg = r_; door = dd; break
        if not sd: rep.append(f"{k}: the pin is on a wall - move it or give a polygon"); continue
        if reg is None:
            dd, area, r_ = tried[0]
            lk = im.copy(); lk[r_ > 0] = (lk[r_ > 0] * 0.4 + np.array([0, 0, 255]) * 0.6).astype(np.uint8)
            cv2.imwrite(os.path.join(a.out, f"leak_{M.disp(k)}.png"), M.shrink(lk, 1600))
            rep.append(f"{k}: the flood leaked even with door {tried[-1][0]}px ({area:.1f}% of the map) - see leak_{M.disp(k)}.png for where it escapes; add a clip box or give a rectangle/polygon"); continue
        if door != items[k][0]: rep.append(f"{k}: flooded with door {door}px (smaller doors leaked) - check that the area stops at its doorways")
        key = None
        for gk, gv in groups.items():
            if (gv["reg"] & reg).any(): key = gk; break
        if key is None: groups[k] = {"reg": reg, "ids": [k], "seeds": [sd], "door": door}
        else: g = groups[key]; g["reg"] |= reg; g["ids"].append(k); g["seeds"].append(sd); g["door"] = max(g["door"], door)
    free = (1 - dark).astype(np.uint8) & (1 - taken)
    for g in groups.values():
        reg = g["reg"]
        if len(g["ids"]) == 1: parts = {g["ids"][0]: reg}
        else:
            mk = np.zeros((H, W), np.int32)
            for i, (sx, sy) in enumerate(g["seeds"], 1): cv2.circle(mk, (sx, sy), 3, i, -1)
            mk[reg == 0] = 0
            seg = watershed(-ndi.distance_transform_edt(reg), mk, mask=reg.astype(bool))
            parts = {k: (seg == i).astype(np.uint8) for i, k in enumerate(g["ids"], 1)}
        for k, r in parts.items():
            for _ in range(max(1, g["door"] // 2 + 1)): r = cv2.dilate(r, np.ones((3, 3), np.uint8)) & np.maximum(free, r)
            r = cv2.dilate(r, np.ones((3, 3), np.uint8)) & (1 - taken)
            r = cv2.morphologyEx(r, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
            out[k] = to_polys(r)
    return out

regions = {}; fl = {}; explicit = {}
for k, v in rough.items():
    if k.startswith("!"): continue
    nosnap = rough.get("!" + k) == "nosnap"
    polys = []
    if v == "flood": fl[k] = (a.door, None); continue
    if isinstance(v, dict) and v.get("flood"): fl[k] = (int(v.get("door", a.door)), v.get("clip")); explicit[k] = "door" in v; continue
    if isinstance(v, list):
        for s_ in v:
            if s_ and isinstance(s_[0], (int, float)) and len(s_) == 4: polys.append(rect_poly(s_ if nosnap else snap_rect(s_)))
            elif s_ and isinstance(s_[0], list): polys.append([[round(x, 2), round(y, 2)] for x, y in s_])
    if polys: regions[k] = polys
    elif v != []: rep.append(f"{k}: no area")
taken = np.zeros((H, W), np.uint8)
for polys in regions.values():
    for p in polys: cv2.fillPoly(taken, [np.array([[int(x / 100 * W), int(y / 100 * H)] for x, y in p], np.int32)], 1)
for k, polys in floods(fl, taken).items():
    if polys: regions[k] = polys
    else: rep.append(f"{k}: no area")

# checks
masks = {}
for k, polys in regions.items():
    m = np.zeros((H, W), np.uint8)
    for p in polys: cv2.fillPoly(m, [np.array([[int(x / 100 * W), int(y / 100 * H)] for x, y in p], np.int32)], 1)
    masks[k] = m
    if k in pins:
        x, y = [int(v) for v in M.to_px(pins[k], W, H)]
        r = int(S * 0.01)
        if not m[max(0, y - r):y + r, max(0, x - r):x + r].any(): rep.append(f"{k}: the pin is outside the room's area")
for k in pins:
    if k not in regions and k not in rough: rep.append(f"{k}: no shape given (add it to ROUGH, or [] for no area)")
ks = list(masks)
for i in range(len(ks)):
    for j in range(i + 1, len(ks)):
        o = (masks[ks[i]] & masks[ks[j]]).sum()
        if o and o > 0.25 * min(masks[ks[i]].sum(), masks[ks[j]].sum()): rep.append(f"{ks[i]} and {ks[j]} overlap a lot")
M.jsave(regions, os.path.join(a.out, "regions.json"))
ov = im.copy(); lay = im.copy()
for i, k in enumerate(pins if pins else regions):
    col = tuple(int(c * 255) for c in colorsys.hsv_to_rgb((i * 0.137) % 1, 0.85, 0.95))
    for p in regions.get(k, []):
        q = np.array([[int(x / 100 * W), int(y / 100 * H)] for x, y in p], np.int32)
        cv2.fillPoly(lay, [q], col); cv2.polylines(ov, [q], True, col, 2)
ov = cv2.addWeighted(lay, 0.4, ov, 0.6, 0); fs = max(0.45, S / 1500)
for k, p in pins.items():
    x, y = [int(v) for v in M.to_px(p, W, H)]; t = k[::-1] if any('֐' <= ch <= '׿' for ch in k) else k
    cv2.circle(ov, (x, y), 4, (0, 0, 0), -1)
    cv2.putText(ov, t, (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, fs, (255, 255, 255), 4, cv2.LINE_AA)
    cv2.putText(ov, t, (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, fs, (0, 0, 0), 1, cv2.LINE_AA)
cv2.imwrite(os.path.join(a.out, "rooms_preview.png"), M.shrink(ov, 2000))
open(os.path.join(a.out, "rooms_report.txt"), "w").write("\n".join(rep) + "\n")
print(f"{len(regions)} rooms with an area." + ("\n" + "\n".join(rep) if rep else ""))
