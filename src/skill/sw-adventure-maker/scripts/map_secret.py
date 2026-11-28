#!/usr/bin/env python3
"""Hide secret rooms on the players' map, and make the patch that shows each one when it is found.

Usage:
  python3 map_secret.py PLAYERS_IN.jpg SPEC.json PLAYERS_OUT.jpg OUT_DIR

PLAYERS_IN  the players' picture after map_players.py (numbers erased, secret rooms still drawn).
SPEC.json   one entry per secret room, all coordinates in percent (read them off map_grid.py):
  {
    "14": {
      "fills": [                                  areas to paint over, each with the look to paint
        {"poly": [[x,y], [x,y], ...], "like": [x, y]},     like = a point whose surface it should look like:
        {"poly": [[...]], "like": [x, y]}                    plain paper outside the dungeon, rock hatching, floor...
      ],
      "walls": [                                  wall lines to draw where the secret door/passage was
        {"from": [x, y], "to": [x, y], "like": [x, y]}      like = a point ON the existing wall this line
      ],                                                    continues: its thickness and colour are copied
                                                            and the line is moved sideways onto it
                                                            ("align": false keeps it where given)
      "box": [x0, y0, x1, y1]                     optional: the patch area (default: around the fills)
    }
  }
Writes PLAYERS_OUT.jpg (secret rooms hidden), OUT_DIR/patch-<id>.png (the room as it looks before hiding,
cut from PLAYERS_IN), OUT_DIR/patches.json (for map_json.py --patches), and OUT_DIR/secret_check.png:
for each room, before | hidden | hidden + patch (the last must look like the first).
Look at the check picture: the hidden version must show no trace of the room or its door, the new
wall must line up with the wall it continues, and the painted area must blend into its surroundings.
"""
import sys, os, json, argparse
import cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maplib as M

ap = argparse.ArgumentParser(); ap.add_argument("inp"); ap.add_argument("spec"); ap.add_argument("out"); ap.add_argument("dir")
ap.add_argument("--margin", type=float, default=0.4, help="patch box margin around the fills, percent")
a = ap.parse_args(); os.makedirs(a.dir, exist_ok=True)
src = M.load(a.inp); H, W = src.shape[:2]; S = min(H, W)
im = src.copy(); spec = M.jload(a.spec)
px = lambda p: (int(round(p[0] / 100 * W)), int(round(p[1] / 100 * H)))
g = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)

def texture_like(pt, shape_hw):
    """a picture of shape_hw filled with the surface found around pt: a sample square, mirror-tiled"""
    x, y = px(pt); r = max(12, S // 30)
    # shrink the sample until it is uniform enough (no walls cutting through it)
    for rr in (r, int(r * .7), int(r * .5), int(r * .35)):
        X0, Y0, X1, Y1 = max(0, x - rr), max(0, y - rr), min(W, x + rr), min(H, y + rr)
        s = src[Y0:Y1, X0:X1]
        gs = g[Y0:Y1, X0:X1]
        if gs.size and np.percentile(gs, 5) > np.percentile(g, 2) + 25 or rr == int(r * .35): break
    tile = np.concatenate([s, s[:, ::-1]], 1); tile = np.concatenate([tile, tile[::-1]], 0)
    h, w = shape_hw
    reps = (h // tile.shape[0] + 2, w // tile.shape[1] + 2, 1)
    big = np.tile(tile, reps)
    oy, ox = np.random.randint(0, tile.shape[0]), np.random.randint(0, tile.shape[1])
    return big[oy:oy + h, ox:ox + w]

def wall_style(wl):
    """thickness, colour and position of the existing wall at wl["like"], measured across the new line's direction.
    The new line is moved sideways onto that wall's centre line, so it continues it exactly."""
    f, t = np.array(px(wl["from"]), float), np.array(px(wl["to"]), float)
    d = t - f; L = np.hypot(*d) or 1; d /= L; n = np.array([-d[1], d[0]])
    lk = np.array(px(wl.get("like", wl["from"])), float); r = max(10, S // 50)
    prof = []
    for k in range(-r, r + 1):
        q = lk + n * k; x, y = int(round(q[0])), int(round(q[1]))
        prof.append(g[min(H - 1, max(0, y)), min(W - 1, max(0, x))])
    prof = np.array(prof, float); i0 = int(np.argmin(prof[r // 2: r + r // 2 + 1])) + r // 2
    thr = prof.min() + 0.5 * (np.median(prof) - prof.min())
    lo = i0
    while lo > 0 and prof[lo - 1] < thr: lo -= 1
    hi = i0
    while hi < len(prof) - 1 and prof[hi + 1] < thr: hi += 1
    th = max(2, hi - lo + 1); c = (lo + hi) / 2 - r
    centre = lk + n * c
    shift = np.dot(centre - f, n) if wl.get("align", True) else 0.0
    cols = []
    for k in range(lo, hi + 1):
        q = lk + n * (k - r); x, y = int(round(q[0])), int(round(q[1]))
        cols.append(src[min(H - 1, max(0, y)), min(W - 1, max(0, x))])
    col = tuple(int(v) for v in np.median(np.array(cols), axis=0))
    return th, col, tuple(int(round(v)) for v in f + n * shift), tuple(int(round(v)) for v in t + n * shift)

patches, tiles = [], []
for rid, sp in spec.items():
    union = np.zeros((H, W), np.uint8)
    for f in sp.get("fills", []):
        m = np.zeros((H, W), np.uint8); cv2.fillPoly(m, [np.array([px(p) for p in f["poly"]], np.int32)], 255)
        union = cv2.max(union, m)
        ys, xs = np.nonzero(m)
        if not len(xs): continue
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        tex = texture_like(f["like"], (y1 - y0, x1 - x0))
        feather = max(3, S // 300) | 1
        al = cv2.GaussianBlur(m[y0:y1, x0:x1], (feather * 2 + 1, feather * 2 + 1), 0).astype(np.float32)[..., None] / 255
        im[y0:y1, x0:x1] = (tex * al + im[y0:y1, x0:x1] * (1 - al)).astype(np.uint8)
    for wl in sp.get("walls", []):
        th, col, p0, p1 = wall_style(wl)
        cv2.line(im, p0, p1, col, th, cv2.LINE_8)
        union = cv2.max(union, cv2.line(np.zeros((H, W), np.uint8), p0, p1, 255, th + 4))
    ys, xs = np.nonzero(union)
    if not len(xs): print(f"{rid}: nothing to hide"); continue
    if sp.get("box"): bx = sp["box"]
    else:
        mg = a.margin
        bx = [max(0, xs.min() / W * 100 - mg), max(0, ys.min() / H * 100 - mg), min(100, (xs.max() + 1) / W * 100 + mg), min(100, (ys.max() + 1) / H * 100 + mg)]
    bx = [round(v, 2) for v in bx]
    X0, Y0, X1, Y1 = int(bx[0] / 100 * W), int(bx[1] / 100 * H), int(np.ceil(bx[2] / 100 * W)), int(np.ceil(bx[3] / 100 * H))
    pf = os.path.join(a.dir, f"patch-{M.disp(rid)}.png")
    cv2.imwrite(pf, src[Y0:Y1, X0:X1])
    patches.append({"room": rid, "box": bx, "file": pf})
    # check: before | hidden | hidden with the patch
    pad = int(0.25 * max(X1 - X0, Y1 - Y0)); cx0, cy0, cx1, cy1 = max(0, X0 - pad), max(0, Y0 - pad), min(W, X1 + pad), min(H, Y1 + pad)
    before, hid = src[cy0:cy1, cx0:cx1], im[cy0:cy1, cx0:cx1]
    withp = hid.copy(); withp[Y0 - cy0:Y1 - cy0, X0 - cx0:X1 - cx0] = src[Y0:Y1, X0:X1]
    cv2.rectangle(withp, (X0 - cx0, Y0 - cy0), (X1 - cx0 - 1, Y1 - cy0 - 1), (0, 140, 255), 1)
    k = 320 / max(before.shape[:2]); rs = lambda z: cv2.resize(z, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC if k > 1 else cv2.INTER_AREA)
    row = np.hstack([rs(before), np.full((rs(before).shape[0], 6, 3), 255, np.uint8), rs(hid), np.full((rs(before).shape[0], 6, 3), 255, np.uint8), rs(withp)])
    row = cv2.copyMakeBorder(row, 24, 6, 4, 4, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    cv2.putText(row, f"room {M.disp(rid)}: before | hidden | hidden + patch", (6, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    tiles.append(row)
ext = os.path.splitext(a.out)[1].lower()
cv2.imwrite(a.out, im, [cv2.IMWRITE_JPEG_QUALITY, 90] if ext in (".jpg", ".jpeg") else [])
M.jsave(patches, os.path.join(a.dir, "patches.json"))
if tiles:
    w = max(t.shape[1] for t in tiles); tiles = [cv2.copyMakeBorder(t, 0, 0, 0, w - t.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) for t in tiles]
    cv2.imwrite(os.path.join(a.dir, "secret_check.png"), np.vstack(tiles))
print(f"hid {len(patches)} room(s) -> {a.out}; patches in {os.path.join(a.dir, 'patches.json')}; look at secret_check.png")
