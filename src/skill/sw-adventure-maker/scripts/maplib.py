"""Shared helpers for the map scripts. Coordinates in files are always percent of the
image width/height (0-100), from the top-left corner - the format the app uses."""
import json, cv2, numpy as np

def load(path):
    im = cv2.imread(path)
    if im is None: raise SystemExit(f"cannot read image {path}")
    return im

def gray_norm(im):
    """grayscale with the page lighting flattened (photographed pages are uneven)"""
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    k = 31 if min(g.shape) > 600 else 15
    bg = cv2.medianBlur(g, k)
    bg = cv2.max(bg, g)
    return cv2.divide(g, bg, scale=255)

def ink(im, thr=150):
    return (gray_norm(im) < thr).astype(np.uint8)

def to_px(p, W, H): return (p[0] / 100 * W, p[1] / 100 * H)
def to_pct(x, y, W, H): return [round(x / W * 100, 2), round(y / H * 100, 2)]

def strip_lines(m, L):
    """remove straight horizontal/vertical runs longer than L pixels (walls, grid) from a 0/1 mask"""
    L = max(5, int(L))
    h = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (L, 1)))
    v = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, L)))
    return cv2.subtract(m, cv2.max(h, v))

def glyph_clusters(m, hmin, hmax, long_max=None, short_max=None):
    """connected components shaped like characters, grouped into labels.
    returns [(box [x0,y0,x1,y1], median glyph size)]"""
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    gl = []
    for k in range(1, n):
        x, y, w, h, a = st[k]
        big, small = max(w, h), min(w, h)
        if not (hmin <= big <= hmax) or a < 6: continue
        fill = a / float(w * h)
        if fill > 0.92 or fill < 0.1: continue
        if small > big * 1.0 and fill < 0.2: continue
        gl.append([x, y, x + w, y + h, big])
    long_max = long_max or hmax * 3.4; short_max = short_max or hmax * 1.4
    used = [False] * len(gl); out = []
    for i in range(len(gl)):
        if used[i]: continue
        box = gl[i][:4]; sizes = [gl[i][4]]; used[i] = True; grew = True
        while grew:
            grew = False
            for j in range(len(gl)):
                if used[j]: continue
                c = gl[j]; s = max(sizes + [c[4]]); gap = 0.6 * s
                dx = max(c[0] - box[2], box[0] - c[2], 0); dy = max(c[1] - box[3], box[1] - c[3], 0)
                if dx <= gap and dy <= gap:
                    nb = [min(box[0], c[0]), min(box[1], c[1]), max(box[2], c[2]), max(box[3], c[3])]
                    L, Sh = max(nb[2] - nb[0], nb[3] - nb[1]), min(nb[2] - nb[0], nb[3] - nb[1])
                    if L > long_max or Sh > short_max: continue
                    box = nb; sizes.append(c[4]); used[j] = True; grew = True
        out.append((box, float(np.median(sizes))))
    return out

def snap(im, pt_pct, radius_pct=2.5, hmin=None, hmax=None, m=None):
    """move a rough point to the centre of the printed label nearest to it.
    returns (centre_pct, box_pct or None, moved_pct)"""
    H, W = im.shape[:2]; S = min(H, W)
    hmin = hmin or max(5, S * 0.007); hmax = hmax or S * 0.06
    x, y = to_px(pt_pct, W, H); R = int(radius_pct / 100 * max(W, H))
    X0, Y0, X1, Y1 = max(0, int(x - R)), max(0, int(y - R)), min(W, int(x + R)), min(H, int(y + R))
    mm = (m if m is not None else ink(im))[Y0:Y1, X0:X1].copy()
    best = None
    for variant in (strip_lines(mm, hmax * 1.4), mm):
        for b, _sz in glyph_clusters(variant, hmin, hmax):
            cx, cy = (b[0] + b[2]) / 2 + X0, (b[1] + b[3]) / 2 + Y0
            d = ((cx - x) ** 2 + (cy - y) ** 2) ** .5
            if d <= R and (best is None or d < best[0]): best = (d, cx, cy, [b[0] + X0, b[1] + Y0, b[2] + X0, b[3] + Y0])
        if best: break
    if not best: return pt_pct, None, 0
    d, cx, cy, b = best
    return to_pct(cx, cy, W, H), [round(b[0] / W * 100, 2), round(b[1] / H * 100, 2), round(b[2] / W * 100, 2), round(b[3] / H * 100, 2)], round(d / max(W, H) * 100, 2)

def jload(p, default=None):
    try: return json.load(open(p, encoding="utf-8"))
    except FileNotFoundError:
        if default is not None: return default
        raise
def jsave(o, p): json.dump(o, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def shrink(img, maxside=1800):
    s = maxside / max(img.shape[:2])
    return cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else img

HEB = dict(zip("אבגדהוזחטיכלמנסעפצקרשת", ["a","b","g","d","h","v","z","ch","t","y","k","l","m","n","s","e","p","tz","q","r","sh","t"]))
def disp(k):
    """an id as OpenCV can draw it (it has no Hebrew letters): 5א -> 5a"""
    return "".join(HEB.get(ch, ch) for ch in str(k))
