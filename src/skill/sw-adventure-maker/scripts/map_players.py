#!/usr/bin/env python3
"""Make the players' copy of a map: erase the room numbers and the DM-only marks.

Usage:
  python3 map_players.py MAP.jpg LABELS.json OUT.jpg [--extra EXTRA.json] [--pad 1] [--dark 140]

LABELS.json  {"id": [x0,y0,x1,y1], ...} percent boxes (map_pins.py writes it; "_" keys are extra marks)
EXTRA.json   more boxes to erase: [[x0,y0,x1,y1], ...] or {"name": [x0,y0,x1,y1]} - secret-door "S"
             marks, trap "X"/"T" marks, a DM legend, a title. A box marked {"box": [...], "fill": true}
             is painted over completely with the colour around it (for a whole legend panel).
Only dark ink inside each box is repainted from its surroundings, so floor lines around the number
mostly survive. Writes OUT.jpg and OUT_check.png (before/after of every box) - look at it.
A secret door drawn as a wall gap or a special door symbol is not erased by this: draw the plain wall
in an image editor, or leave it and say so in map.players.note.
"""
import sys, os, argparse
import cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maplib as M

ap = argparse.ArgumentParser()
ap.add_argument("map"); ap.add_argument("labels"); ap.add_argument("out")
ap.add_argument("--extra"); ap.add_argument("--pad", type=float, default=1.0, help="px around each box, in units of 2px")
ap.add_argument("--dark", type=int, default=140)
a = ap.parse_args()
im = M.load(a.map); H, W = im.shape[:2]
boxes = [(k, b, False) for k, b in M.jload(a.labels).items() if b]
if a.extra:
    ex = M.jload(a.extra)
    items = ex.items() if isinstance(ex, dict) else enumerate(ex)
    for k, b in items:
        if isinstance(b, dict): boxes.append((f"x{k}", b["box"], bool(b.get("fill"))))
        else: boxes.append((f"x{k}", b, False))
g = M.gray_norm(im)
mask = np.zeros((H, W), np.uint8); fillmask = np.zeros((H, W), np.uint8)
pad = int(2 * a.pad)
for k, b, fill in boxes:
    x0, y0, x1, y1 = int(b[0] / 100 * W) - pad, int(b[1] / 100 * H) - pad, int(np.ceil(b[2] / 100 * W)) + pad, int(np.ceil(b[3] / 100 * H)) + pad
    x0, y0 = max(0, x0), max(0, y0)
    if fill: fillmask[y0:y1, x0:x1] = 255
    else: mask[y0:y1, x0:x1] = np.maximum(mask[y0:y1, x0:x1], (g[y0:y1, x0:x1] < a.dark).astype(np.uint8) * 255)
mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=1)
out = cv2.inpaint(im, cv2.max(mask, fillmask), 5, cv2.INPAINT_TELEA)
ext = os.path.splitext(a.out)[1].lower()
cv2.imwrite(a.out, out, [cv2.IMWRITE_JPEG_QUALITY, 88] if ext in (".jpg", ".jpeg") else [])
tiles = []
for k, b, fill in boxes:
    cx, cy = (b[0] + b[2]) / 2 / 100 * W, (b[1] + b[3]) / 2 / 100 * H
    r = max((b[2] - b[0]) / 100 * W, (b[3] - b[1]) / 100 * H) * 1.3 + 8
    X0, Y0, X1, Y1 = int(max(0, cx - r)), int(max(0, cy - r)), int(min(W, cx + r)), int(min(H, cy + r))
    A = cv2.resize(im[Y0:Y1, X0:X1], (110, 110)); B = cv2.resize(out[Y0:Y1, X0:X1], (110, 110))
    t = np.hstack([A, np.full((110, 4, 3), 255, np.uint8), B]); t = cv2.copyMakeBorder(t, 18, 4, 4, 4, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    cv2.putText(t, M.disp(k), (4, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA); tiles.append(t)
if tiles:
    cols = 6
    while len(tiles) % cols: tiles.append(np.full_like(tiles[0], 255))
    cv2.imwrite(os.path.splitext(a.out)[0] + "_check.png", np.vstack([np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]))
print(f"erased {len(boxes)} boxes -> {a.out}")
