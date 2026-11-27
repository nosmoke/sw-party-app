#!/usr/bin/env python3
"""Pack one or more books and their pictures into the single file the app imports.

Usage:  python3 bundle.py OUT.sw-adventure.json BOOK.json [BOOK2.json ...] [--images DIR]

Every picture path in the book ("books/x-map.jpg") is looked up by file name in --images (default:
the book's folder). Pictures are shrunk to at most 2400px on the long side and re-saved as JPEG
(PNG kept for patches with transparency) so the file stays small; the app shrinks anything above
about 900KB anyway. Runs validate.py's checks first and stops on errors."""
import sys, os, re, json, base64, io, subprocess, argparse
ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("books", nargs="+"); ap.add_argument("--images")
ap.add_argument("--max", type=int, default=2400)
a = ap.parse_args()
here = os.path.dirname(os.path.abspath(__file__))
from PIL import Image
IMG = re.compile(r'"([^"\s]{1,300}\.(?:jpe?g|png|webp|gif))"', re.I)
books = []
for bp in a.books:
    r = subprocess.run([sys.executable, os.path.join(here, "validate.py"), bp] + ([a.images] if a.images else []))
    if r.returncode: sys.exit(f"{bp}: fix the errors first")
    b = json.load(open(bp, encoding="utf-8")); d = a.images or os.path.dirname(os.path.abspath(bp))
    imgs = {}
    for ref in sorted(set(IMG.findall(json.dumps(b, ensure_ascii=False)))):
        f = os.path.join(d, os.path.basename(ref))
        if not os.path.exists(f): print(f"  (no file for {ref}; the app will drop it)"); continue
        im = Image.open(f); keep_png = im.mode in ("RGBA", "LA", "P") and ref.lower().endswith(".png")
        s = a.max / max(im.size)
        if s < 1: im = im.resize((round(im.size[0] * s), round(im.size[1] * s)), Image.LANCZOS)
        buf = io.BytesIO()
        if keep_png: im.save(buf, "PNG", optimize=True); mt = "image/png"
        else: im.convert("RGB").save(buf, "JPEG", quality=85, optimize=True); mt = "image/jpeg"
        imgs[ref] = f"data:{mt};base64," + base64.b64encode(buf.getvalue()).decode()
        print(f"  {ref}: {im.size[0]}x{im.size[1]}, {len(buf.getvalue())//1024} KB")
    books.append({"book": b, "images": imgs})
json.dump({"format": "sw-adventure", "version": 1, "books": books}, open(a.out, "w", encoding="utf-8"), ensure_ascii=False)
print(f"{a.out}: {os.path.getsize(a.out)//1024} KB, books: {', '.join(x['book']['id'] for x in books)}")
