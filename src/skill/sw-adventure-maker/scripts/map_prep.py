#!/usr/bin/env python3
"""Prepare the DM map picture: cut it out of a page, turn it upright, join several levels.

  python3 map_prep.py crop  PAGE.png OUT.jpg X0 Y0 X1 Y1 [--rotate 90|180|270]
        cut the box (percent of the page, read off map_grid.py) and optionally rotate
  python3 map_prep.py join  OUT.jpg A.png B.png [C.png ...] [--vertical] [--gap 40]
        put several level maps next to each other (one book has one map picture)
  python3 map_prep.py fit   IN.png OUT.jpg [--long 1800]
        scale to a good working size: 1400-2400 px on the long side (small scans are enlarged)
All modes save JPEG (quality 90) unless OUT ends in .png.
"""
import sys, os, argparse
import cv2, numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("mode", choices=["crop", "join", "fit"]); ap.add_argument("args", nargs="+")
ap.add_argument("--rotate", type=int, default=0); ap.add_argument("--vertical", action="store_true"); ap.add_argument("--gap", type=int, default=40)
ap.add_argument("--long", type=int, default=1800)
a = ap.parse_args()
def save(img, p):
    cv2.imwrite(p, img, [] if p.lower().endswith(".png") else [cv2.IMWRITE_JPEG_QUALITY, 90]); print(p, img.shape[1], "x", img.shape[0])
def rot(img, r):
    return img if not r else cv2.rotate(img, {90: cv2.ROTATE_90_CLOCKWISE, 180: cv2.ROTATE_180, 270: cv2.ROTATE_90_COUNTERCLOCKWISE}[r])
if a.mode == "crop":
    src, out, *box = a.args; x0, y0, x1, y1 = map(float, box)
    im = cv2.imread(src); H, W = im.shape[:2]
    c = im[int(y0 / 100 * H):int(y1 / 100 * H), int(x0 / 100 * W):int(x1 / 100 * W)]
    save(rot(c, a.rotate), out)
elif a.mode == "join":
    out, *ins = a.args; ims = [rot(cv2.imread(p), a.rotate) for p in ins]
    if a.vertical:
        w = max(i.shape[1] for i in ims); ims = [cv2.copyMakeBorder(i, 0, a.gap, 0, w - i.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) for i in ims]
        save(np.vstack(ims), out)
    else:
        h = max(i.shape[0] for i in ims); ims = [cv2.copyMakeBorder(i, 0, h - i.shape[0], 0, a.gap, cv2.BORDER_CONSTANT, value=(255, 255, 255)) for i in ims]
        save(np.hstack(ims), out)
else:
    src, out = a.args; im = rot(cv2.imread(src), a.rotate); s = a.long / max(im.shape[:2])
    if 0.75 < s < 1.35 and max(im.shape[:2]) <= 2400: s = 1
    save(cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA) if s != 1 else im, out)
