#!/usr/bin/env python3
"""Get pages and text out of the source material.

Usage:
  python3 extract.py SOURCE... OUT_DIR [--dpi 150]

SOURCE can be a PDF, a Word/ODT/RTF document, a text/markdown file, or page photos/scans
(jpg/png/webp/heic). Several sources are processed in the order given.
Writes to OUT_DIR:
  pages/p001.png ...   one picture per page (PDF pages rendered; photos copied, straightened to
                       upright by their EXIF orientation). Look at them for layout, boxed read-aloud
                       text, tables and maps.
  text/p001.txt ...    the text layer of each page when there is one (PDF with text, Word).
                       Scans and photos have no text layer: read the page pictures instead.
  images/              pictures embedded in PDF/Word files (candidate maps), with their page.
  summary.txt          what was found: pages, which have text, embedded images and their sizes.
"""
import sys, os, subprocess, shutil, glob, argparse, json
ap = argparse.ArgumentParser()
ap.add_argument("src", nargs="+"); ap.add_argument("--dpi", type=int, default=150)
a = ap.parse_args()
*srcs, out = a.src
for d in ("pages", "text", "images"): os.makedirs(os.path.join(out, d), exist_ok=True)
n = 0; summ = []
def have(x): return shutil.which(x) is not None

def pdf(path):
    global n
    start = n
    if have("pdftoppm"):
        tmp = os.path.join(out, "_pdf"); os.makedirs(tmp, exist_ok=True)
        subprocess.run(["pdftoppm", "-r", str(a.dpi), "-png", path, os.path.join(tmp, "pg")], check=True)
        for f in sorted(glob.glob(os.path.join(tmp, "pg-*.png")), key=lambda p: int(p.rsplit("-", 1)[1][:-4])):
            n += 1; shutil.move(f, os.path.join(out, "pages", f"p{n:03d}.png"))
        shutil.rmtree(tmp, ignore_errors=True)
    else:
        try:
            import fitz
            doc = fitz.open(path)
            for pg in doc:
                n += 1; pg.get_pixmap(dpi=a.dpi).save(os.path.join(out, "pages", f"p{n:03d}.png"))
        except ImportError:
            summ.append(f"{path}: cannot render pages (no pdftoppm, no PyMuPDF) - pip install pymupdf"); return
    pages = n - start
    for i in range(1, pages + 1):
        t = ""
        if have("pdftotext"):
            t = subprocess.run(["pdftotext", "-layout", "-f", str(i), "-l", str(i), path, "-"], capture_output=True, text=True).stdout
        else:
            try:
                from pypdf import PdfReader; t = PdfReader(path).pages[i - 1].extract_text() or ""
            except Exception: t = ""
        open(os.path.join(out, "text", f"p{start + i:03d}.txt"), "w").write(t)
    if have("pdfimages"):
        subprocess.run(["pdfimages", "-png", "-p", path, os.path.join(out, "images", f"{os.path.basename(path)}")], capture_output=True)
    withtext = sum(1 for i in range(start + 1, n + 1) if len(open(os.path.join(out, "text", f"p{i:03d}.txt")).read().strip()) > 40)
    summ.append(f"{path}: pages {start+1}-{n}; {withtext} with a text layer" + ("" if withtext else " (a scan: read the page pictures)"))

def office(path):
    global n
    tmp = os.path.join(out, "_doc"); os.makedirs(tmp, exist_ok=True)
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice:
        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", tmp, path], capture_output=True, timeout=240)
        pdfs = glob.glob(os.path.join(tmp, "*.pdf"))
        if pdfs: pdf(pdfs[0])
    if have("pandoc"):
        md = subprocess.run(["pandoc", path, "-t", "gfm", "--extract-media", os.path.join(out, "images", os.path.basename(path))], capture_output=True, text=True).stdout
        open(os.path.join(out, "text", os.path.basename(path) + ".md"), "w").write(md)
        summ.append(f"{path}: full text as markdown in text/{os.path.basename(path)}.md (headings and tables kept)")
    elif not soffice:
        try:
            import docx
            d = docx.Document(path); open(os.path.join(out, "text", os.path.basename(path) + ".txt"), "w").write("\n".join(p.text for p in d.paragraphs))
            summ.append(f"{path}: text only (python-docx)")
        except Exception as e: summ.append(f"{path}: cannot read ({e})")
    shutil.rmtree(tmp, ignore_errors=True)

def photo(path):
    global n
    try:
        from PIL import Image, ImageOps
        try:
            import pillow_heif; pillow_heif.register_heif_opener()
        except ImportError: pass
        im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        n += 1; im.save(os.path.join(out, "pages", f"p{n:03d}.png"))
        summ.append(f"{path}: page p{n:03d} ({im.size[0]}x{im.size[1]}), a photo/scan: read the picture")
    except Exception as e: summ.append(f"{path}: cannot open ({e})")

for s in srcs:
    ext = os.path.splitext(s)[1].lower()
    if ext == ".pdf": pdf(s)
    elif ext in (".docx", ".doc", ".odt", ".rtf"): office(s)
    elif ext in (".txt", ".md"): shutil.copy(s, os.path.join(out, "text", os.path.basename(s))); summ.append(f"{s}: text copied")
    elif ext in (".jpg", ".jpeg", ".png", ".webp", ".heic", ".tif", ".tiff", ".bmp"): photo(s)
    else: summ.append(f"{s}: unknown type, skipped")
imgs = []
try:
    from PIL import Image
    for f in sorted(glob.glob(os.path.join(out, "images", "**", "*.*"), recursive=True)):
        try: w, h = Image.open(f).size; imgs.append(f"{os.path.relpath(f, out)} {w}x{h}")
        except Exception: pass
except ImportError: pass
summ.append(f"{n} page pictures in pages/."); summ += ["embedded images (big ones may be maps):"] + [i for i in imgs if "x" in i][:80]
open(os.path.join(out, "summary.txt"), "w").write("\n".join(summ) + "\n"); print("\n".join(summ))
