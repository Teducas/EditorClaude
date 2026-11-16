# Mini motor de motion graphics (PIL + numpy -> ffmpeg) con la identidad de la marca del proyecto.
# Todo se dibuja a 3x y se reduce (bordes suaves). Cada escena es una función f(t) -> Image RGB.
# Llamar a setup(P) ANTES de importar un archivo de escenas (los colores salen de marcas/<cliente>/brand.json).
import math, os, subprocess, random, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 30
SS = 3
ROOT = None          # carpeta del proyecto
ASSETS = None        # carpeta de la marca (logos)
ENCODER = None

def hx(h, a=255):
    h = h.lstrip("#"); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)

# Colores por rol. Los nombres históricos (NAVY, ORANGE…) se mantienen como alias de cada rol.
NAVY = PRIMARY = hx("#14355a"); DEEP = hx("#0a1d36"); STEEL = MUTED = hx("#608ba7")
ORANGE = ACCENT = hx("#e4893f"); SAND = ACCENT2 = hx("#e0a96d"); ICE = LIGHT = hx("#a9c0d6"); WHITE = hx("#ffffff")
GREY, GREEN, RED = hx("#7d8ea3"), hx("#3fbf7f"), hx("#e05252")

FONTS = {"black": "C:/Windows/Fonts/seguibl.ttf", "bold": "C:/Windows/Fonts/segoeuib.ttf",
         "semi": "C:/Windows/Fonts/seguisb.ttf", "reg": "C:/Windows/Fonts/segoeui.ttf",
         "emoji": "C:/Windows/Fonts/seguiemj.ttf", "sym": "C:/Windows/Fonts/seguisym.ttf"}

BRAND = {}

def logo(w=None, variant="logo_light"):
    """Logo de la marca (por defecto la versión clara, para fondos oscuros)."""
    return load(BRAND.get(variant) or BRAND.get("logo_light"), w)

def setup(P):
    """Carga colores, fuentes y logos de la marca del proyecto P."""
    global ROOT, ASSETS, NAVY, PRIMARY, DEEP, STEEL, MUTED, ORANGE, ACCENT, SAND, ACCENT2, ICE, LIGHT
    ROOT, ASSETS = P.dir, P.brand_dir
    c = P.brand.get("colors", {})
    NAVY = PRIMARY = hx(c.get("primary", "#14355a")); DEEP = hx(c.get("deep", "#0a1d36"))
    STEEL = MUTED = hx(c.get("muted", "#608ba7")); ORANGE = ACCENT = hx(c.get("accent", "#e4893f"))
    SAND = ACCENT2 = hx(c.get("accent2", "#e0a96d")); ICE = LIGHT = hx(c.get("light", "#a9c0d6"))
    FONTS.update(P.brand.get("fonts", {}))
    BRAND.clear(); BRAND.update(P.brand)
    _fc.clear()
_fc = {}
def font(kind, size):
    k = (kind, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(FONTS[kind], size)
    return _fc[k]

# ---------- easing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, t0, d): return clamp((t - t0) / d) if d > 0 else float(t >= t0)
def ease_out(x): return 1 - (1 - x) ** 3
def ease_in(x): return x ** 3
def ease_io(x): return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2
def back(x, s=1.70158): x -= 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def elastic(x):
    if x in (0, 1): return x
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi / 3)) + 1
def lerp(a, b, x): return a + (b - a) * x

def pop(t, t0, d=0.45):
    """(escala, alpha) de una entrada con rebote que empieza en t0."""
    x = prog(t, t0, d)
    return (back(x) if x < 1 else 1.0), clamp(x * 2.5)

# ---------- sprites ----------
class Sprite:
    """Imagen RGBA con ancla en su centro."""
    def __init__(self, img): self.img = img
    @property
    def size(self): return self.img.size

def canvas_ss(w, h): return Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
def down(img): return img.resize((img.width // SS, img.height // SS), Image.LANCZOS)

def rrect(w, h, r, fill, outline=None, width=0, shadow=0):
    pad = shadow * 2
    im = canvas_ss(w + pad * 2, h + pad * 2)
    d = ImageDraw.Draw(im)
    o = pad * SS
    d.rounded_rectangle([o, o, o + w * SS - 1, o + h * SS - 1], r * SS, fill=fill, outline=outline, width=width * SS)
    out = down(im)
    if shadow:
        sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        sd.rounded_rectangle([pad, pad + shadow // 2, pad + w, pad + h + shadow // 2], r, fill=(0, 0, 0, 110))
        sh = sh.filter(ImageFilter.GaussianBlur(shadow * 0.6))
        out = Image.alpha_composite(sh, out)
    return Sprite(out)

def circle(d, fill, outline=None, width=0):
    im = canvas_ss(d, d); dr = ImageDraw.Draw(im)
    dr.ellipse([0, 0, d * SS - 1, d * SS - 1], fill=fill, outline=outline, width=width * SS)
    return Sprite(down(im))

def text(s, kind, size, fill=WHITE, stroke=0, stroke_fill=None, spacing=0.12, align="center", shadow=False):
    f = font(kind, size)
    lines = s.split("\n")
    asc, desc = f.getmetrics()
    lh = int((asc + desc) * (1 + spacing))
    widths = [f.getbbox(l)[2] - f.getbbox(l)[0] if l else 0 for l in lines]
    w = max(widths) + stroke * 2 + 8
    h = lh * len(lines) + stroke * 2 + 8
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        x = 20 + stroke + 4 + ((w - 8 - stroke * 2 - widths[i]) / 2 if align == "center" else (w - 8 - stroke * 2 - widths[i]) if align == "right" else 0)
        x -= f.getbbox(l)[0] if l else 0
        d.text((x, 20 + stroke + 4 + i * lh), l, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    if shadow:
        a = im.split()[3].filter(ImageFilter.GaussianBlur(8))
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.putalpha(a.point(lambda v: int(v * 0.55)))
        sh = sh.transform(sh.size, Image.AFFINE, (1, 0, 0, 0, 1, -4))
        im = Image.alpha_composite(sh, im)
    return Sprite(im.crop(im.getbbox()) if im.getbbox() else im)

def load(name, w=None):
    im = Image.open(os.path.join(ASSETS, name)).convert("RGBA")
    if w: im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    return Sprite(im)

def draw_lines(w, h, segs, color, width, round_caps=True):
    """Polilíneas en un lienzo w x h. segs: lista de listas de puntos."""
    im = canvas_ss(w, h); d = ImageDraw.Draw(im)
    for pts in segs:
        p = [(x * SS, y * SS) for x, y in pts]
        d.line(p, fill=color, width=width * SS, joint="curve")
        if round_caps:
            r = width * SS / 2
            for x, y in (p[0], p[-1]):
                d.ellipse([x - r, y - r, x + r, y + r], fill=color)
    return Sprite(down(im))

def poly(w, h, pts, fill):
    im = canvas_ss(w, h); d = ImageDraw.Draw(im)
    d.polygon([(x * SS, y * SS) for x, y in pts], fill=fill)
    return Sprite(down(im))

def path_partial(pts, x):
    """Primer tramo (fracción x de la longitud) de una polilínea."""
    if x <= 0: return pts[:1]
    L = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    tot, goal, acc = sum(L), sum(L) * clamp(x), 0
    out = [pts[0]]
    for i, l in enumerate(L):
        if acc + l >= goal:
            k = (goal - acc) / l if l else 0
            out.append((lerp(pts[i][0], pts[i + 1][0], k), lerp(pts[i][1], pts[i + 1][1], k)))
            return out
        acc += l; out.append(pts[i + 1])
    return out

# ---------- composición ----------
def place(frame, sp, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if alpha <= 0.003 or scale <= 0.003: return
    im = sp.img if isinstance(sp, Sprite) else sp
    if abs(scale - 1) > 1e-3:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if abs(rot) > 0.05:
        im = im.rotate(rot, Image.BICUBIC, expand=True)
    if alpha < 0.999:
        a = im.split()[3].point(lambda v, k=alpha: int(v * k)); im = im.copy(); im.putalpha(a)
    frame.alpha_composite(im, (int(round(cx - im.width / 2)), int(round(cy - im.height / 2)))) if 0 else _safe(frame, im, cx, cy)

def _safe(frame, im, cx, cy):
    x, y = int(round(cx - im.width / 2)), int(round(cy - im.height / 2))
    # recorte a los bordes del lienzo
    l, t = max(0, -x), max(0, -y)
    r, b = min(im.width, W - x), min(im.height, H - y)
    if r <= l or b <= t: return
    frame.alpha_composite(im.crop((l, t, r, b)), (x + l, y + t))

def crop_reveal(sp, frac, direction="x"):
    """Revela una fracción del sprite (barra que crece, subrayado...)."""
    im = sp.img
    if direction == "x":
        w = max(1, int(im.width * clamp(frac))); return Sprite(im.crop((0, 0, w, im.height)))
    h = max(1, int(im.height * clamp(frac))); return Sprite(im.crop((0, im.height - h, im.width, im.height)))

def background(seed=3, glow=(960, 540)):
    """Fondo de marca: degradado navy, resplandor naranja suave, rejilla y bokeh."""
    rng = random.Random(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    t = np.clip(yy / H * 0.6 + np.abs(xx - W / 2) / W * 0.7, 0, 1)[..., None]
    img = np.array(NAVY[:3], np.float32) * (1 - t) + np.array(DEEP[:3], np.float32) * t
    d = np.sqrt(((xx - glow[0]) / 900) ** 2 + ((yy - glow[1]) / 650) ** 2)[..., None]
    img += (np.array(ORANGE[:3], np.float32) - img) * np.clip(1 - d, 0, 1) ** 2.4 * 0.22
    base = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(lay)
    for x in range(0, W, 80): dr.line([(x, 0), (x, H)], fill=(169, 192, 214, 14), width=1)
    for y in range(0, H, 80): dr.line([(0, y), (W, y)], fill=(169, 192, 214, 14), width=1)
    for _ in range(40):
        x, y, r = rng.randint(0, W), rng.randint(0, H), rng.randint(3, 10)
        c = (228, 137, 63, rng.randint(25, 70)) if rng.random() < 0.5 else (169, 192, 214, rng.randint(20, 50))
        dr.ellipse([x - r, y - r, x + r, y + r], fill=c)
    lay = lay.filter(ImageFilter.GaussianBlur(1.5))
    base = Image.alpha_composite(base, lay)
    v = np.sqrt(((xx - W / 2) / (W * 0.7)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2)
    arr = np.asarray(base).astype(np.float32)
    arr[..., :3] *= (1 - np.clip((v - 0.55) * 0.8, 0, 0.45))[..., None]
    return Image.fromarray(arr.astype(np.uint8), "RGBA")

def drift(bg, t, amp=14, speed=0.06):
    """Ligero movimiento de cámara del fondo (zoom lento)."""
    s = 1 + 0.03 * math.sin(t * speed * 2 * math.pi) + 0.02 * t / 10
    w, h = int(W / s), int(H / s)
    x = int((W - w) / 2 + amp * math.sin(t * 0.4)); y = int((H - h) / 2 + amp * 0.5 * math.cos(t * 0.3))
    return bg.crop((x, y, x + w, y + h)).resize((W, H), Image.BILINEAR)

def render(path, dur, scene, fade_in=0.0, fade_out=0.0, preview_at=None):
    """Renderiza la escena a MP4 H.264 1080p30 (QSV) o, con preview_at, guarda PNGs de control."""
    if preview_at:
        ims = [scene(t).convert("RGB").resize((640, 360), Image.LANCZOS) for t in preview_at]
        sheet = Image.new("RGB", (640 * min(4, len(ims)), 360 * ((len(ims) + 3) // 4)))
        for i, im in enumerate(ims): sheet.paste(im, ((i % 4) * 640, (i // 4) * 360))
        sheet.save(path); return path
    global ENCODER
    if ENCODER is None:
        from prepare_media import pick_encoder
        ENCODER = pick_encoder()
    enc, eargs = ENCODER
    n = int(round(dur * FPS))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", enc, *eargs, "-pix_fmt", "nv12" if enc == "h264_qsv" else "yuv420p", "-movflags", "+faststart", path], stdin=subprocess.PIPE)
    for i in range(n):
        t = i / FPS
        im = scene(t).convert("RGB")
        k = 1.0
        if fade_in and t < fade_in: k = t / fade_in
        if fade_out and t > dur - fade_out: k = min(k, (dur - t) / fade_out)
        if k < 1: im = Image.blend(Image.new("RGB", im.size, DEEP[:3]), im, clamp(k))
        p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait()
    return path

def check_mark(size, color=None, width=None):
    w = width or max(6, size // 7)
    return draw_lines(size, size, [[(size * 0.18, size * 0.55), (size * 0.42, size * 0.78), (size * 0.84, size * 0.25)]], color or GREEN, w)

def cross_mark(size, color=None, width=None):
    w = width or max(6, size // 7)
    return draw_lines(size, size, [[(size * 0.2, size * 0.2), (size * 0.8, size * 0.8)], [(size * 0.8, size * 0.2), (size * 0.2, size * 0.8)]], color or RED, w)
