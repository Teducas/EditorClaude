"""Marca a partir de lo que el diseñador pegue en marcas/<cliente>/, en cualquier formato.

  run.py marca         marcas/<cliente>
      Analiza todo (PNG, JPG, WEBP, PSD, SVG, PDF, AI, PPTX, DOCX, ZIP, fuentes, textos) y deja en
      marcas/<cliente>/_revision/:  hoja_*.jpg (miniaturas + paleta de cada archivo), inventario.txt
      (colores candidatos, posibles logos, fuentes) y las imágenes extraídas de PDF/AI/SVG/PPTX/ZIP.

  run.py marca-aplicar marcas/<cliente> --logo <archivo> --colores primary=#hex,accent=#hex[,...]
                       [--nombre "Cliente"] [--fuentes black=..,bold=..,semi=..,reg=..] [--logo-tal-cual]
      Genera brand.json, logo_light.png (versión blanca, sin fondo), logo_color.png y muestra.jpg.
      Los roles que falten (deep, panel, light, muted, accent2) se derivan de primary y accent.
"""
import os, re, sys, json, shutil, zipfile, subprocess, collections, colorsys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

IMG_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".psd", ".ico"}
PDF_EXT = {".pdf", ".ai"}
OFFICE_EXT = {".pptx", ".docx", ".xlsx", ".potx", ".dotx"}
FONT_EXT = {".ttf", ".otf"}
TEXT_EXT = {".txt", ".md", ".css", ".scss", ".json", ".html", ".htm", ".csv", ".xml", ".ase.txt"}
GENERATED = {"brand.json", "logo_light.png", "logo_color.png", "muestra.jpg"}
NO_LEIBLE = {".eps": "EPS", ".indd": "InDesign", ".fig": "Figma", ".sketch": "Sketch", ".xd": "Adobe XD", ".cdr": "CorelDRAW", ".heic": "HEIC", ".key": "Keynote"}
ROLES = ["primary", "deep", "accent", "accent2", "light", "muted", "panel"]
HEX_RE = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
RGB_RE = re.compile(r"\bR(?:GB)?\s*[:=]?\s*(\d{1,3})\s*[,/\s]\s*(?:G\s*[:=]?\s*)?(\d{1,3})\s*[,/\s]\s*(?:B\s*[:=]?\s*)?(\d{1,3})\b", re.I)

# ---------------------------------------------------------------- utilidades de color
def to_hex(rgb): return "#%02x%02x%02x" % tuple(int(round(v)) for v in rgb[:3])
def from_hex(h):
    h = h.strip().lstrip("#")
    if len(h) == 3: h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def lum(rgb):
    def ch(c):
        c /= 255; return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in rgb[:3]); return 0.2126 * r + 0.7152 * g + 0.0722 * b
def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True); return (la + 0.05) / (lb + 0.05)
def mix(a, b, t): return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
def hls(rgb): return colorsys.rgb_to_hls(*(v / 255 for v in rgb[:3]))
def from_hls(h, l, s): return tuple(v * 255 for v in colorsys.hls_to_rgb(h, max(0, min(1, l)), max(0, min(1, s))))
def kind_of(rgb):
    h, l, s = hls(rgb)
    if l > 0.93: return "blanco"
    if l < 0.08: return "negro"
    if s < 0.12: return "gris"
    return "color"

def palette(img, n=6):
    """[(hex, peso 0-1)] de una imagen, ignorando píxeles transparentes."""
    im = img.convert("RGBA"); im.thumbnail((220, 220))
    a = np.asarray(im)
    px = a[a[..., 3] > 128][:, :3]
    if len(px) < 20: return []
    q = Image.fromarray(px.reshape(1, -1, 3).astype(np.uint8), "RGB").quantize(colors=n, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()[: n * 3]
    counts = collections.Counter(q.getdata())
    tot = sum(counts.values())
    out = [(to_hex(pal[i * 3:i * 3 + 3]), c / tot) for i, c in counts.most_common(n) if c / tot >= 0.02]
    return out

def has_alpha(img):
    if img.mode not in ("RGBA", "LA", "PA") and not (img.mode == "P" and "transparency" in img.info): return False
    a = np.asarray(img.convert("RGBA"))[..., 3]
    return a.min() < 250

# ---------------------------------------------------------------- lectores por formato
class Scan:
    def __init__(self, folder):
        self.folder = os.path.abspath(folder)
        self.rev = os.path.join(self.folder, "_revision")
        self.items = []          # (etiqueta, PIL.Image | None, paleta, nota)
        self.hex_text = collections.Counter()
        self.fonts = []          # (ruta relativa, familia, estilo)
        self.skipped = []        # (archivo, motivo)
        self.texts = []          # archivos de texto extraídos (para que Claude los lea)

    def rel(self, p): return os.path.relpath(p, self.folder).replace("\\", "/")

    def add_image(self, label, img, note=""):
        try:
            img.load()
            if img.mode in ("P", "LA", "L", "CMYK", "I;16", "I"): img = img.convert("RGBA")
            self.items.append((label, img, palette(img), note))
        except Exception as e:
            self.skipped.append((label, f"imagen ilegible ({e.__class__.__name__})"))

    def add_text_colors(self, text, weight=1):
        for m in HEX_RE.finditer(text):
            self.hex_text[to_hex(from_hex(m.group(1)))] += weight
        for m in RGB_RE.finditer(text):
            v = [int(x) for x in m.groups()]
            if all(0 <= x <= 255 for x in v): self.hex_text[to_hex(v)] += weight

    def save_extract(self, img, name):
        os.makedirs(self.rev, exist_ok=True)
        p = os.path.join(self.rev, name)
        img.save(p); return p

    # --- formatos
    def raster(self, path):
        im = Image.open(path)
        n = getattr(im, "n_frames", 1)
        if n > 1 and im.format == "GIF": im.seek(0)
        self.add_image(self.rel(path), im.copy(), "transparente" if has_alpha(im) else "")

    def pdf(self, path):
        try:
            import fitz
        except ImportError:
            self.skipped.append((self.rel(path), "falta pymupdf (ejecuta setup.ps1)")); return
        try:
            doc = fitz.open(path, filetype="pdf")
        except Exception:
            self.skipped.append((self.rel(path), "no se pudo abrir (si es .ai, guárdalo con «Crear archivo compatible con PDF» o expórtalo a PDF/SVG/PNG)")); return
        base = os.path.splitext(os.path.basename(path))[0]
        txt = []
        seen = set()
        for i, page in enumerate(doc):
            if i >= 12: break
            t = page.get_text(); txt.append(f"--- página {i + 1} ---\n{t}"); self.add_text_colors(t, 3)
            if i < 8:
                z = min(2.0, 1400 / max(page.rect.width, 1))
                pm = page.get_pixmap(matrix=fitz.Matrix(z, z), alpha=False)
                im = Image.frombytes("RGB", (pm.width, pm.height), pm.samples)
                p = self.save_extract(im, f"{base}_p{i + 1}.png")
                self.add_image(f"{self.rel(path)} · pág. {i + 1}", im, "página")
            for info in page.get_images(full=True):
                xref, smask = info[0], info[1]
                if xref in seen: continue
                seen.add(xref)
                try:
                    pix = fitz.Pixmap(doc, xref)
                    if pix.width < 80 or pix.height < 40: continue
                    if smask:
                        pix = fitz.Pixmap(pix, fitz.Pixmap(doc, smask))
                    if pix.n - pix.alpha >= 4: pix = fitz.Pixmap(fitz.csRGB, pix)
                    mode = "RGBA" if pix.alpha else "RGB"
                    im = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
                    self.save_extract(im, f"{base}_img{xref}.png")
                    self.add_image(f"{self.rel(path)} · imagen {xref}", im, "imagen incrustada" + (" transparente" if pix.alpha else ""))
                except Exception:
                    pass
        if any(s.strip() for s in txt):
            os.makedirs(self.rev, exist_ok=True)
            tp = os.path.join(self.rev, f"{base}_texto.txt")
            open(tp, "w", encoding="utf-8").write("\n".join(txt)[:60000]); self.texts.append(self.rel(tp))

    def svg(self, path):
        src = open(path, encoding="utf-8", errors="ignore").read()
        self.add_text_colors(src, 3)
        out = os.path.join(self.rev, os.path.splitext(os.path.basename(path))[0] + "_svg.png")
        os.makedirs(self.rev, exist_ok=True)
        if svg_to_png(path, out):
            self.add_image(self.rel(path), Image.open(out).copy(), "vectorial (convertido a PNG)")
        else:
            self.skipped.append((self.rel(path), "no se pudo convertir el SVG a imagen; los colores sí se leyeron"))

    def office(self, path):
        base = os.path.splitext(os.path.basename(path))[0]
        try:
            z = zipfile.ZipFile(path)
        except zipfile.BadZipFile:
            self.skipped.append((self.rel(path), "archivo dañado")); return
        for n in z.namelist():
            low = n.lower()
            if "/theme/" in low and low.endswith(".xml"):
                x = z.read(n).decode("utf-8", "ignore")
                for m in re.finditer(r'srgbClr val="([0-9A-Fa-f]{6})"', x): self.hex_text["#" + m.group(1).lower()] += 2
            elif re.search(r"/(slides|document|slidemasters|slidelayouts)/.*\.xml$", low) or low.endswith("document.xml"):
                x = z.read(n).decode("utf-8", "ignore")
                for m in re.finditer(r'(?:srgbClr val|w:color w:val|w:fill)="([0-9A-Fa-f]{6})"', x): self.hex_text["#" + m.group(1).lower()] += 1
                self.add_text_colors(re.sub(r"<[^>]+>", " ", x), 2)
            elif "/media/" in low and os.path.splitext(low)[1] in IMG_EXT | {".svg", ".emf", ".wmf"}:
                ext = os.path.splitext(low)[1]
                if ext in (".emf", ".wmf"): continue
                data = z.read(n)
                if len(data) < 2000: continue
                os.makedirs(self.rev, exist_ok=True)
                p = os.path.join(self.rev, f"{base}_{os.path.basename(n)}")
                open(p, "wb").write(data)
                if ext == ".svg": self.svg(p)
                else:
                    try: self.add_image(f"{self.rel(path)} · {os.path.basename(n)}", Image.open(p).copy(), "imagen del documento")
                    except Exception: pass

    def font(self, path):
        try:
            f = ImageFont.truetype(path, 40); fam, sty = f.getname()
            self.fonts.append((self.rel(path), fam, sty))
        except Exception:
            self.skipped.append((self.rel(path), "fuente ilegible"))

    def text(self, path):
        self.add_text_colors(open(path, encoding="utf-8", errors="ignore").read(), 3)

    def unzip(self, path):
        dest = os.path.join(self.rev, "_zip", os.path.splitext(os.path.basename(path))[0])
        os.makedirs(dest, exist_ok=True)
        with zipfile.ZipFile(path) as z:
            for n in z.namelist():
                target = os.path.abspath(os.path.join(dest, n))
                if not target.startswith(os.path.abspath(dest) + os.sep) or n.endswith("/"): continue
                if "__MACOSX" in n or os.path.basename(n).startswith("."): continue
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with z.open(n) as s, open(target, "wb") as d: shutil.copyfileobj(s, d)
        self.walk(dest)

    def file(self, path):
        name = os.path.basename(path); ext = os.path.splitext(name)[1].lower()
        if name in GENERATED or name.startswith((".", "~$")) or name.lower() in ("desktop.ini", "thumbs.db"): return
        try:
            if ext in IMG_EXT: self.raster(path)
            elif ext in PDF_EXT: self.pdf(path)
            elif ext == ".svg": self.svg(path)
            elif ext in OFFICE_EXT: self.office(path)
            elif ext in FONT_EXT: self.font(path)
            elif ext == ".zip": self.unzip(path)
            elif ext in TEXT_EXT: self.text(path)
            elif ext in NO_LEIBLE: self.skipped.append((self.rel(path), f"{NO_LEIBLE[ext]}: pide una exportación a PDF, SVG o PNG"))
            else: self.skipped.append((self.rel(path), "formato no reconocido"))
        except Exception as e:
            self.skipped.append((self.rel(path), f"error al leer ({e.__class__.__name__}: {e})"))

    def walk(self, folder):
        for root, dirs, files in os.walk(folder):
            dirs[:] = sorted(d for d in dirs if os.path.join(root, d) != self.rev and not d.startswith("."))
            for f in sorted(files): self.file(os.path.join(root, f))

def svg_to_png(svg, out, size=1200):
    """SVG -> PNG transparente recortado. Primero PyMuPDF (Windows y Mac); si falla, Chrome/Edge sin ventana."""
    try:
        import fitz
        d = fitz.open(svg); pg = d[0]
        z = size / max(pg.rect.width, pg.rect.height, 1)
        pm = pg.get_pixmap(matrix=fitz.Matrix(z, z), alpha=True)
        im = Image.frombytes("RGBA", (pm.width, pm.height), pm.samples)
        bb = im.getbbox()
        if bb:
            im.crop(bb).save(out); return True
    except Exception:
        pass
    from platforms import browser
    edge = browser()
    if not edge: return False
    import pathlib, tempfile
    src = open(svg, encoding="utf-8", errors="ignore").read()
    src = re.sub(r"<\?xml[^>]*\?>|<!DOCTYPE[^>]*>", "", src)
    # carpeta temporal sin acentos ni espacios: Edge falla con algunas rutas
    tmp = tempfile.mkdtemp(prefix="svg_")
    html, shot = os.path.join(tmp, "s.html"), os.path.join(tmp, "s.png")
    open(html, "w", encoding="utf-8").write(
        "<!doctype html><html><head><meta charset='utf-8'><style>html,body{margin:0;background:transparent}"
        f"#b{{width:{size}px;height:{size}px;display:flex;align-items:center;justify-content:center}}"
        f"#b svg{{width:{size}px;height:{size}px}}</style></head><body><div id='b'>{src}</div></body></html>")
    try:
        subprocess.run([edge, "--headless", "--disable-gpu", "--hide-scrollbars", "--default-background-color=00000000",
                        f"--window-size={size},{size}", f"--screenshot={shot}", pathlib.Path(html).as_uri()],
                       capture_output=True, timeout=60)
        if os.path.exists(shot): shutil.move(shot, out)
    except Exception:
        return False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if not os.path.exists(out): return False
    im = Image.open(out).convert("RGBA")
    bb = im.getbbox()
    if not bb: return False
    im.crop(bb).save(out); return True

# ---------------------------------------------------------------- hoja de revisión
def checker(w, h, s=16):
    im = Image.new("RGB", (w, h), (236, 238, 242)); d = ImageDraw.Draw(im)
    for y in range(0, h, s):
        for x in range(0, w, s):
            if (x // s + y // s) % 2: d.rectangle([x, y, x + s - 1, y + s - 1], fill=(214, 218, 225))
    return im

def ui_font(size, bold=False):
    from platforms import default_fonts
    f = default_fonts().get("bold" if bold else "reg")
    if f and os.path.exists(f): return ImageFont.truetype(f, size)
    return ImageFont.load_default()

def contact_sheets(scan):
    TW, TH, PAD, COLS, ROWS = 380, 260, 24, 4, 3
    cell_h = TH + 92
    pages = [scan.items[i:i + COLS * ROWS] for i in range(0, len(scan.items), COLS * ROWS)] or [[]]
    out = []
    for pi, page in enumerate(pages):
        sheet = Image.new("RGB", (PAD + COLS * (TW + PAD), 70 + ROWS * (cell_h + PAD)), "white")
        d = ImageDraw.Draw(sheet)
        d.text((PAD, 18), f"Marca · {os.path.basename(scan.folder)} · hoja {pi + 1}/{len(pages)}  (fondo a cuadros = transparente)", fill=(20, 26, 43), font=ui_font(26, True))
        for k, (label, img, pal, note) in enumerate(page):
            cx, cy = PAD + (k % COLS) * (TW + PAD), 70 + (k // COLS) * (cell_h + PAD)
            bg = checker(TW, TH); th = img.convert("RGBA"); th.thumbnail((TW - 16, TH - 16))
            bg.paste(th, ((TW - th.width) // 2, (TH - th.height) // 2), th)
            sheet.paste(bg, (cx, cy)); d.rectangle([cx, cy, cx + TW - 1, cy + TH - 1], outline=(200, 205, 214))
            num = pi * COLS * ROWS + k + 1
            d.text((cx, cy + TH + 6), f"{num}. {label[-46:]}", fill=(20, 26, 43), font=ui_font(17, True))
            d.text((cx, cy + TH + 28), (note or f"{img.width}×{img.height}")[:52], fill=(100, 110, 125), font=ui_font(16))
            for j, (hx, w) in enumerate(pal[:6]):
                x0 = cx + j * 62; d.rectangle([x0, cy + TH + 52, x0 + 56, cy + TH + 84], fill=from_hex(hx), outline=(190, 195, 205))
        p = os.path.join(scan.rev, f"hoja_{pi + 1}.jpg"); sheet.save(p, quality=88); out.append(p)
    return out

def analizar(folder):
    folder = os.path.abspath(folder)
    if not os.path.isdir(folder): sys.exit(f"No existe la carpeta {folder}")
    rev = os.path.join(folder, "_revision")
    if os.path.isdir(rev): shutil.rmtree(rev)
    os.makedirs(rev)
    s = Scan(folder); s.walk(folder)
    sheets = contact_sheets(s)
    # colores: de imágenes (por peso) + de textos (códigos escritos en manuales/SVG/PPTX)
    score = collections.Counter()
    for label, img, pal, note in s.items:
        w = 0.4 if "página" in note else 1.0
        for hx, frac in pal: score[hx] += frac * w
    for hx, n in s.hex_text.items(): score[hx] += 0.5 * n
    merged = []
    for hx, sc in score.most_common():
        rgb = from_hex(hx)
        if any(sum((a - b) ** 2 for a, b in zip(rgb, from_hex(m[0]))) < 18 ** 2 for m in merged): continue
        merged.append((hx, sc))
    logos = [(i + 1, lbl, note) for i, (lbl, img, pal, note) in enumerate(s.items)
             if ("transparente" in note or re.search(r"logo|isotipo|imagotipo|marca|brand|icon|símbolo|simbolo", lbl, re.I)) and "página" not in note]
    L = [f"MARCA: {os.path.basename(folder)}", f"Archivos analizados: {len(s.items)} imágenes, {len(s.fonts)} fuentes, {len(s.skipped)} sin leer", ""]
    L += ["COLORES CANDIDATOS (más peso primero; tipo según luminosidad/saturación)"]
    L += [f"  {hx}  {kind_of(from_hex(hx)):6s}  peso {sc:5.2f}" + ("  [escrito en un documento]" if s.hex_text.get(hx) else "") for hx, sc in merged[:16]]
    L += ["", "CÓDIGOS DE COLOR ESCRITOS EN DOCUMENTOS (manual, SVG, PPTX…)"]
    L += [f"  {hx}  ×{n}" for hx, n in s.hex_text.most_common(20)] or ["  (ninguno)"]
    L += ["", "POSIBLES LOGOS (número de la hoja · archivo · nota)"]
    L += [f"  {n}. {lbl}  ({note})" for n, lbl, note in logos] or ["  (ninguno obvio: mira las hojas)"]
    L += ["", "TODAS LAS IMÁGENES (número de la hoja)"]
    L += [f"  {i + 1}. {lbl}  [{img.width}×{img.height}] {note}" for i, (lbl, img, pal, note) in enumerate(s.items)]
    L += ["", "FUENTES"]
    from platforms import DEFAULT_FONT_LABEL
    L += [f"  {p}  →  {fam} {sty}" for p, fam, sty in s.fonts] or [f"  (ninguna: se usará {DEFAULT_FONT_LABEL})"]
    if s.texts: L += ["", "TEXTO EXTRAÍDO (léelo si es un manual de marca)"] + [f"  {t}" for t in s.texts]
    if s.skipped: L += ["", "NO SE PUDIERON LEER"] + [f"  {f}: {why}" for f, why in s.skipped]
    L += ["", "HOJAS DE REVISIÓN"] + [f"  {os.path.relpath(p, folder)}" for p in sheets]
    open(os.path.join(rev, "inventario.txt"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))

# ---------------------------------------------------------------- aplicar
def resolve(folder, p):
    for cand in (p, os.path.join(folder, p), os.path.join(folder, "_revision", p)):
        if os.path.exists(cand): return os.path.abspath(cand)
    sys.exit(f"No encuentro el archivo {p!r} (ruta relativa a la carpeta de la marca o a _revision)")

def load_logo(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".svg":
        out = os.path.join(os.path.dirname(path), "_tmp_logo.png")
        if not svg_to_png(path, out, 1600): sys.exit("No se pudo convertir el SVG del logo")
        im = Image.open(out).convert("RGBA"); os.remove(out); return im
    if ext in PDF_EXT:
        import fitz
        doc = fitz.open(path, filetype="pdf"); pg = doc[0]
        z = 2000 / max(pg.rect.width, pg.rect.height)
        pm = pg.get_pixmap(matrix=fitz.Matrix(z, z), alpha=True)
        return Image.frombytes("RGBA", (pm.width, pm.height), pm.samples)
    return Image.open(path).convert("RGBA")

def cut_background(im):
    """Si el logo no tiene transparencia, quita el color de fondo (el de los bordes)."""
    a = np.asarray(im).astype(np.float32)
    if a[..., 3].min() < 250: return im, False
    border = np.concatenate([a[0, :, :3], a[-1, :, :3], a[:, 0, :3], a[:, -1, :3]])
    bg = np.median(border, axis=0)
    dist = np.sqrt(((a[..., :3] - bg) ** 2).sum(-1))
    alpha = np.clip((dist - 14) / (70 - 14), 0, 1) * 255
    out = a.copy(); out[..., 3] = alpha
    return Image.fromarray(out.astype(np.uint8), "RGBA"), True

def trim(im, pad=8):
    bb = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    if not bb: sys.exit("El logo quedó vacío al quitar el fondo: elige otra versión del logo")
    im = im.crop(bb)
    return ImageOps.expand(im, pad, fill=(0, 0, 0, 0))

def derive(colors):
    c = {k: from_hex(v) for k, v in colors.items()}
    if "primary" not in c: sys.exit("Falta al menos --colores primary=#xxxxxx")
    P = c["primary"]; h, l, s = hls(P)
    if "accent" not in c:  # complementario cálido si no hay acento
        c["accent"] = from_hls((h + 0.5) % 1, 0.6, max(0.6, s))
    A = c["accent"]; ha, la, sa = hls(A)
    c.setdefault("deep", from_hls(h, max(0.06, min(l, 0.4) * 0.55), s))
    c.setdefault("panel", from_hls(h, max(0.07, min(l, 0.4) * 0.7), s * 0.9))
    c.setdefault("light", from_hls(h, 0.82, min(0.45, s)))
    c.setdefault("muted", from_hls(h, 0.55, s * 0.45))
    c.setdefault("accent2", from_hls(ha, min(0.85, la + 0.15), sa * 0.85))
    return {k: to_hex(c[k]) for k in ROLES}

def auto_fonts(folder):
    fs = []
    for root, _, files in os.walk(folder):
        if "_revision" in root and "_zip" not in root: continue
        for f in files:
            if os.path.splitext(f)[1].lower() in FONT_EXT:
                p = os.path.join(root, f)
                try: fam, sty = ImageFont.truetype(p, 40).getname()
                except Exception: continue
                fs.append((p, fam, sty.lower()))
    if not fs: return {}
    fam = collections.Counter(f[1] for f in fs).most_common(1)[0][0]
    fs = [f for f in fs if f[1] == fam and "italic" not in f[2] and "oblique" not in f[2]]
    def pick(*keys):
        for k in keys:
            for p, _, sty in fs:
                if re.search(k, sty): return p
    reg = pick(r"^regular$", r"^book$", r"^roman$", r"normal", r"regular") or fs[0][0]
    semi = pick(r"semi ?bold", r"demi", r"medium") or reg
    bold = pick(r"^bold$", r"(?<!semi )(?<!extra )(?<!ultra )bold") or semi
    black = pick(r"black", r"heavy", r"extra ?bold", r"ultra ?bold") or bold
    rel = lambda p: os.path.relpath(p, folder).replace("\\", "/")
    return {"black": rel(black), "bold": rel(bold), "semi": rel(semi), "reg": rel(reg)}

def kv(s):
    out = {}
    for part in (s or "").split(","):
        if "=" in part:
            k, v = part.split("=", 1); out[k.strip()] = v.strip()
    return out

def sample(folder, brand, logo_white):
    """Muestra de cómo se verá la marca en el video (tarjeta, rótulo, subtítulo, logo y paleta)."""
    c = {k: from_hex(v) for k, v in brand["colors"].items()}
    fonts = {k: (v if os.path.isabs(v) else os.path.join(folder, v)) for k, v in brand.get("fonts", {}).items()}
    from platforms import default_fonts
    DEF = default_fonts()
    F = lambda k, s: ImageFont.truetype(fonts[k] if k in fonts and os.path.exists(fonts[k]) else DEF[k], s)
    W, H = 1600, 900
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    for y in range(H): d.line([(0, y), (W, y)], fill=tuple(int(v) for v in mix(c["primary"], c["deep"], y / H)))
    im = im.convert("RGBA")
    lg = logo_white.copy(); lg.thumbnail((140, 90)); im.alpha_composite(lg, (W - lg.width - 40, 36))
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([70, 150, 690, 560], 26, fill=c["panel"] + (235,), outline=c["light"] + (90,), width=2)
    cd.text((110, 185), "TRES CLAVES", font=F("black", 46), fill=c["accent"])
    for i, (t, hi) in enumerate([("Constancia", False), ("Método", True), ("Comunidad", False)]):
        y = 275 + i * 88
        cd.ellipse([110, y + 8, 146, y + 44], fill=c["accent"] if hi else c["muted"])
        cd.text((168, y), t, font=F("bold", 42), fill=c["accent2"] if hi else (255, 255, 255))
    cd.rounded_rectangle([70, 640, 640, 760], 20, fill=c["panel"] + (240,))
    cd.rectangle([70, 640, 82, 760], fill=c["accent"])
    cd.text((110, 655), "Nombre Apellido", font=F("black", 44), fill=(255, 255, 255))
    cd.text((110, 712), "Cargo · Empresa", font=F("semi", 30), fill=c["light"])
    im.alpha_composite(card)
    d = ImageDraw.Draw(im)
    f = F("black", 58); words = [("Así se verán ", (255, 255, 255)), ("tus subtítulos", c["accent"])]
    x = 820
    for t, col in words:
        d.text((x, 640), t, font=f, fill=col, stroke_width=5, stroke_fill=c["deep"]); x += d.textlength(t, font=f)
    for i, k in enumerate(ROLES):
        x0 = 820 + i * 108; d.rounded_rectangle([x0, 170, x0 + 92, 262], 14, fill=c[k], outline=(255, 255, 255, 120), width=2)
        d.text((x0, 272), k, font=ui_font(20, True), fill=(255, 255, 255)); d.text((x0, 298), brand["colors"][k], font=ui_font(18), fill=c["light"])
    d.text((820, 380), brand.get("name", ""), font=F("black", 64), fill=(255, 255, 255))
    d.text((820, 470), "Texto de ejemplo con la tipografía de la marca.", font=F("reg", 32), fill=c["light"])
    out = os.path.join(folder, "muestra.jpg"); im.convert("RGB").save(out, quality=90); return out

def aplicar(folder, argv):
    import argparse
    ap = argparse.ArgumentParser(prog="run.py marca-aplicar")
    ap.add_argument("--logo", required=True); ap.add_argument("--colores", required=True)
    ap.add_argument("--nombre"); ap.add_argument("--fuentes")
    ap.add_argument("--logo-tal-cual", action="store_true", help="no quitar el fondo del logo")
    a = ap.parse_args(argv)
    folder = os.path.abspath(folder)
    cols = kv(a.colores)
    bad = [k for k in cols if k not in ROLES]
    if bad: sys.exit(f"Roles desconocidos: {bad}. Usa: {', '.join(ROLES)}")
    colors = derive(cols)
    if contrast(from_hex(colors["accent"]), from_hex(colors["primary"])) < 2.2:
        print(f"AVISO: el acento {colors['accent']} contrasta poco con el principal {colors['primary']}: elige otro acento más vivo o claro.")
    src = resolve(folder, a.logo)
    im = load_logo(src)
    cut = False
    if not a.logo_tal_cual: im, cut = cut_background(im)
    im = trim(im)
    if max(im.size) > 1600: im.thumbnail((1600, 1600))
    im.save(os.path.join(folder, "logo_color.png"))
    white = im.copy(); arr = np.asarray(white).copy(); arr[..., :3] = 255
    white = Image.fromarray(arr, "RGBA"); white.save(os.path.join(folder, "logo_light.png"))
    fonts = kv(a.fuentes) if a.fuentes else auto_fonts(folder)
    fonts = {k: v for k, v in fonts.items() if k in ("black", "bold", "semi", "reg")}
    brand = {"name": a.nombre or os.path.basename(folder).replace("-", " ").title(), "colors": colors,
             "logo_light": "logo_light.png", "logo_color": "logo_color.png", "source_logo": os.path.relpath(src, folder).replace("\\", "/")}
    if fonts: brand["fonts"] = fonts
    json.dump(brand, open(os.path.join(folder, "brand.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    out = sample(folder, brand, white)
    print("Marca lista:", os.path.join(folder, "brand.json"))
    print("  colores:", ", ".join(f"{k}={v}" for k, v in colors.items()))
    print("  logo:", brand["source_logo"], "(fondo quitado)" if cut else "(ya era transparente)" if not a.logo_tal_cual else "(tal cual)")
    from platforms import DEFAULT_FONT_LABEL
    print("  fuentes:", ", ".join(f"{k}={v}" for k, v in fonts.items()) if fonts else f"{DEFAULT_FONT_LABEL} (no había fuentes de la marca)")
    print("  MUESTRA para aprobar:", out)

if __name__ == "__main__":
    if len(sys.argv) < 3: sys.exit(__doc__)
    cmd, folder = sys.argv[1], sys.argv[2]
    if cmd == "analizar": analizar(folder)
    elif cmd == "aplicar": aplicar(folder, sys.argv[3:])
    else: sys.exit(__doc__)
