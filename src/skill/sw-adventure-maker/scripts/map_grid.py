#!/usr/bin/env python3
"""Draw a percent grid on a map so positions can be read off it by eye.

Usage:
  python3 map_grid.py MAP.jpg OUT_DIR                 whole map, 10% / 5% lines  -> grid_all.png
  python3 map_grid.py MAP.jpg OUT_DIR --tiles 3x2     the map cut in 3x2 zoomed tiles, 1% lines -> grid_r1c1.png ...
  python3 map_grid.py MAP.jpg OUT_DIR --box 40 20 60 35 [--step 0.5]   one zoomed area
Options: --overlay FILE.json   draw pins ({"id":[x,y]}) and regions ({"id":[[[x,y],..],..]}) on top
         --name NAME           output file name (default from the mode)
Lines: red every 10%, orange every 5%, light blue every --step. Numbers along the edges are percent.
"""
import sys, os, argparse, colorsys
import cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maplib as M

ap = argparse.ArgumentParser()
ap.add_argument("map"); ap.add_argument("out")
ap.add_argument("--tiles", default=""); ap.add_argument("--box", nargs=4, type=float)
ap.add_argument("--step", type=float, default=0); ap.add_argument("--overlay", action="append", default=[])
ap.add_argument("--name", default=""); ap.add_argument("--size", type=int, default=1400)
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
im = M.load(a.map); H, W = im.shape[:2]
over = [M.jload(p) for p in a.overlay]

def render(x0, y0, x1, y1, step, name):
    X0, Y0, X1, Y1 = int(x0 / 100 * W), int(y0 / 100 * H), int(np.ceil(x1 / 100 * W)), int(np.ceil(y1 / 100 * H))
    c = im[Y0:Y1, X0:X1].copy(); h, w = c.shape[:2]
    s = a.size / max(w, h); c = cv2.resize(c, (int(w * s), int(h * s)), interpolation=cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA)
    pad = 34; c = cv2.copyMakeBorder(c, pad, 0, pad, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    px = lambda xp: int((xp / 100 * W - X0) * s) + pad
    py = lambda yp: int((yp / 100 * H - Y0) * s) + pad
    for o in over:
        for i, (k, v) in enumerate(o.items()):
            col = tuple(int(q * 255) for q in colorsys.hsv_to_rgb((i * 0.137) % 1, 0.9, 0.85))
            if v and isinstance(v[0], (int, float)) and len(v) == 2:
                cv2.circle(c, (px(v[0]), py(v[1])), 5, (0, 0, 255), -1)
                cv2.putText(c, str(k)[::-1] if any('֐' <= ch <= '׿' for ch in str(k)) else str(k), (px(v[0]) + 6, py(v[1]) - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA)
            elif v:
                for poly in v:
                    if isinstance(poly[0], (int, float)): poly = [[poly[0], poly[1]], [poly[2], poly[1]], [poly[2], poly[3]], [poly[0], poly[3]]]
                    p = np.array([[px(x), py(y)] for x, y in poly], np.int32); cv2.polylines(c, [p], True, col, 2)
                    cv2.putText(c, M.disp(k), (p[0][0] + 3, p[0][1] + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.55, col, 2, cv2.LINE_AA)
    def lines(lo, hi, f, vertical):
        v = np.ceil(lo / step) * step
        while v <= hi + 1e-9:
            q = f(v); major = abs(v / 10 - round(v / 10)) < 1e-6; mid = abs(v / 5 - round(v / 5)) < 1e-6
            col = (0, 0, 230) if major else (0, 140, 255) if mid else (230, 170, 60)
            th = 2 if major else 1
            if vertical:
                cv2.line(c, (q, pad), (q, c.shape[0]), col, th)
                if major or mid or step >= 1: cv2.putText(c, f"{v:g}", (q - 10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.45, col, 1, cv2.LINE_AA)
            else:
                cv2.line(c, (pad, q), (c.shape[1], q), col, th)
                if major or mid or step >= 1: cv2.putText(c, f"{v:g}", (1, q + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, col, 1, cv2.LINE_AA)
            v += step
    lines(x0, x1, px, True); lines(y0, y1, py, False)
    cv2.imwrite(os.path.join(a.out, name), c); print(os.path.join(a.out, name))

if a.box:
    x0, y0, x1, y1 = a.box; span = max(x1 - x0, y1 - y0)
    render(x0, y0, x1, y1, a.step or (0.5 if span <= 15 else 1), a.name or f"grid_{x0:g}_{y0:g}.png")
elif a.tiles:
    cx, cy = [int(v) for v in a.tiles.lower().split("x")]
    ov = 3.0
    for r in range(cy):
        for q in range(cx):
            x0 = max(0, q * 100 / cx - ov); x1 = min(100, (q + 1) * 100 / cx + ov)
            y0 = max(0, r * 100 / cy - ov); y1 = min(100, (r + 1) * 100 / cy + ov)
            render(x0, y0, x1, y1, a.step or 1, f"grid_r{r+1}c{q+1}.png")
else:
    render(0, 0, 100, 100, a.step or 5, a.name or "grid_all.png")
