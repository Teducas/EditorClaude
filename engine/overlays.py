"""Paso 7 · Tarjetas laterales, rótulo de nombre, etiqueta de título y logo como PNG transparentes 1920x1080.
Todo se define en project.json:

  "cards": [
    {"id": "g01", "side": "R", "start": "IMG_0136:4", "end": "IMG_0136:9:e+0.3",
     "header": "¿TE IDENTIFICAS?", "statement": "Si hoy estás *aquí…*"},
    {"id": "g02", "side": "L", "start": "IMG_0138:1", "end": "IMG_0138:13:e+0.4", "header": "TAL VEZ…",
     "icon": "x", "items": [["Llevas *meses*", "IMG_0138:3"], ["…o *años*", "IMG_0138:4"]]}
  ],
  "lower_third": {"title": "Nombre Apellido", "subtitle": "Cargo · Empresa", "start": "IMG_0132:4-0.2", "end": "IMG_0132:16:e+0.6"},
  "title_pill": {"text": "CLASE 1 · BIENVENIDA", "start": 0.3, "end": "IMG_0135:2"},
  "logo_bug": true

*texto* = énfasis en color de acento. Cada punto de una lista aparece cuando se dice su palabra ancla.
Iconos: dot | check | x | num.  Salida: overlays/*.png, overlays/overlays.json y work/overlays_sheet.jpg (control).
"""
import json, os, subprocess
from common import project_from_argv
import mg
from mg import *
from timeline import Timeline

PANEL_W = 480

def rich(line, kind, size, base=None, accent=None):
    base, accent = base or WHITE, accent or mg.ACCENT
    f = font(kind, size); asc, desc = f.getmetrics()
    w = int(f.getlength(line.replace("*", ""))) + 8
    im = Image.new("RGBA", (w, asc + desc + 8), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 2
    for i, p in enumerate(line.split("*")):
        if p:
            d.text((x, 2), p, font=f, fill=accent if i % 2 else base); x += f.getlength(p)
    return Sprite(im)

def wrap(s, kind, size, maxw):
    lines, cur = [], ""
    for w in s.split(" "):
        test = (cur + " " + w).strip()
        if font(kind, size).getlength(test.replace("*", "")) > maxw and cur: lines.append(cur); cur = w
        else: cur = test
    lines.append(cur)
    out, open_ = [], False
    for l in lines:
        l2 = ("*" if open_ else "") + l
        if l2.count("*") % 2: l2 += "*"; open_ = True
        else: open_ = False
        out.append(l2)
    return out

def frame(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))

def main():
    P = project_from_argv(); mg.setup(P); TL = Timeline(P); C = P.cfg
    OUT = P.p("overlays")
    for f in os.listdir(OUT):
        if f.endswith(".png"): os.remove(os.path.join(OUT, f))
    def save(im, name): im.save(os.path.join(OUT, name)); return name
    margin = C.get("card_margin", 50)
    SIDE_X = {"L": margin, "R": W - margin - PANEL_W}; TOP = C.get("card_top", 230)
    spec = []
    for g in C.get("cards", []):
        gid, side = g["id"], g["side"]
        x0 = SIDE_X[side]; inner = x0 + 40; maxw = PANEL_W - 80
        hdr = text(g["header"], "black", 30, WHITE)
        rows = []
        if g.get("statement"):
            rows += [("st", ln) for ln in wrap(g["statement"], "black", 50, maxw)]
        for txt, anchor in g.get("items", []):
            rows.append(("it", wrap(txt, "bold", 38, maxw - 70), TL.at(anchor)))
        h = 120 + sum(66 if r[0] == "st" else 30 + 50 * len(r[1]) for r in rows) + 30
        im = frame()
        place(im, rrect(PANEL_W, h, 30, hx(P.brand["colors"].get("panel", "#0d2547"), 222), outline=hx("#a9c0d6", 70), width=2, shadow=26), x0 + PANEL_W / 2, TOP + h / 2)
        place(im, rrect(8, h - 60, 4, mg.ACCENT), x0 + (8 if side == "L" else PANEL_W - 8), TOP + h / 2)
        pill = rrect(min(hdr.size[0] + 50, PANEL_W - 60), 58, 29, mg.ACCENT)
        place(im, pill, inner + pill.size[0] / 2 - 4, TOP + 58); place(im, hdr, inner + pill.size[0] / 2 - 4, TOP + 56)
        files = {"panel": save(im, f"{gid}_panel.png")}
        y, items, st_im = TOP + 120, [], (frame() if g.get("statement") else None)
        icon = g.get("icon", "dot")
        for r in rows:
            if r[0] == "st":
                sp = rich(r[1], "black", 50); place(st_im, sp, inner + sp.size[0] / 2, y + 30); y += 66; continue
            lines, t = r[1], r[2]; it = frame()
            ic = {"dot": circle(22, mg.ACCENT), "check": check_mark(44, GREEN, 8), "x": cross_mark(40, RED, 8), "num": circle(44, mg.ACCENT)}[icon]
            place(it, ic, inner + 22, y + 32)
            if icon == "num": place(it, text(str(len(items) + 1), "black", 26, WHITE), inner + 22, y + 30)
            for k, ln in enumerate(lines):
                sp = rich(ln, "bold", 38); place(it, sp, inner + 70 + sp.size[0] / 2, y + 30 + k * 50)
            items.append({"file": save(it, f"{gid}_item{len(items) + 1}.png"), "t": t}); y += 30 + 50 * len(lines)
        if st_im: files["statement"] = save(st_im, f"{gid}_statement.png")
        spec.append({"id": gid, "side": side, "start": TL.at(g["start"]), "end": TL.at(g["end"]), **files, "items": items})
    extra = {}
    if C.get("lower_third"):
        lt = C["lower_third"]; im = frame()
        place(im, rrect(760, 150, 24, hx(P.brand["colors"].get("panel", "#0d2547"), 230), shadow=24), 90 + 380, 820)
        place(im, rrect(10, 110, 5, mg.ACCENT), 110, 820)
        n1 = text(lt["title"], "black", 60, WHITE); place(im, n1, 140 + n1.size[0] / 2, 790)
        n2 = text(lt.get("subtitle", ""), "semi", 32, mg.ACCENT2); place(im, n2, 140 + n2.size[0] / 2, 852)
        save(im, "lower_name.png"); extra["lower_name"] = {"start": TL.at(lt["start"]), "end": TL.at(lt["end"])}
    if C.get("title_pill"):
        tp = C["title_pill"]; im = frame(); tt = text(tp["text"], "black", 32, WHITE)
        pl = rrect(tt.size[0] + 60, 66, 33, mg.ACCENT, shadow=14); place(im, pl, 70 + pl.size[0] / 2, 90); place(im, tt, 70 + pl.size[0] / 2, 88)
        save(im, "title_pill.png"); extra["title_pill"] = {"start": TL.at(tp["start"]), "end": TL.at(tp["end"])}
    if C.get("logo_bug", True) and P.brand.get("logo_light"):
        im = frame(); place(im, logo(96), W - 100, 105, 1, 0.85); save(im, "logo_bug.png"); extra["logo_bug"] = True
    json.dump({"groups": spec, **extra}, open(os.path.join(OUT, "overlays.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # hoja de control sobre un fotograma real
    edl = TL.edl; still = P.p("work", "still.png")
    src = P.p("media", edl[0]["clip"] + ".mp4")
    if not os.path.exists(src): src = P.source_file(edl[0]["clip"])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(edl[0]["a"] + 1), "-i", src, "-frames:v", "1", "-vf", "scale=1920:1080", still], check=True)
    base = Image.open(still).convert("RGBA"); thumbs = []
    for g in spec + [{"panel": f, "items": []} for f in ("lower_name.png", "title_pill.png", "logo_bug.png") if os.path.exists(os.path.join(OUT, f))]:
        im = base.copy()
        for f in [g["panel"], g.get("statement")] + [i["file"] for i in g["items"]]:
            if f: im.alpha_composite(Image.open(os.path.join(OUT, f)))
        thumbs.append(im.convert("RGB").resize((480, 270)))
    sheet = Image.new("RGB", (480 * 4, 270 * ((len(thumbs) + 3) // 4)))
    for i, t in enumerate(thumbs): sheet.paste(t, ((i % 4) * 480, (i // 4) * 270))
    sheet.save(P.p("work", "overlays_sheet.jpg"))
    print(f"{len(spec)} tarjetas -> {OUT}  | control: {P.p('work', 'overlays_sheet.jpg')}")

if __name__ == "__main__":
    main()
