# EJEMPLO REAL · Tomas de apoyo del video de bienvenida de Ramón (Ramon Academy).
# Cada escena se sincroniza con palabras concretas del montaje (wt = segundo de una palabra).
# Se ejecuta con: python engine/run.py broll-preview|broll-render projects/<video>
import math
from mg import *
from scenes_api import scene, at

CX, CY = W / 2, H / 2

def wt(clip, i, edge="s"):
    """Atajo del ejemplo: wt("0137", 6) = segundo de la palabra 6 de IMG_0137."""
    return at(f"IMG_{clip}:{i}:{edge}")

def caption_safe_title(s, size=64, color=WHITE):
    return text(s, "black", size, color, shadow=True)

# ---------------------------------------------------------------- 1. LICENCIA
S1, E1 = wt("0137", 0), wt("0137", 12, "e") + 0.15
@scene("01_licencia", S1, E1)
def licencia():
    bg = background(1, (700, 520))
    card = rrect(820, 500, 34, WHITE, shadow=30)
    head = rrect(820, 120, 34, NAVY)
    head_sq = rrect(820, 60, 0, NAVY)
    lic_t = text("LICENCIA", "black", 58, WHITE)
    lic_s = text("REAL ESTATE  ·  AGENTE", "semi", 26, SAND)
    avatar = circle(170, hx("#dfe6ee"))
    av_head = circle(70, hx("#a9b8c8"))
    av_body = rrect(120, 60, 30, hx("#a9b8c8"))
    lines = [rrect(w, 22, 11, hx("#e3e9f0")) for w in (380, 300, 340, 220)]
    stamp = text("APROBADA", "black", 54, ORANGE)
    stamp_box = rrect(stamp.size[0] + 50, stamp.size[1] + 26, 16, (0, 0, 0, 0), outline=ORANGE, width=7)
    q = text("¿Por dónde\ncomenzar?", "black", 84, WHITE, shadow=True)
    qmark = text("?", "black", 150, ORANGE)
    t_apr = wt("0137", 6) - S1          # "licencia"
    t_q = wt("0137", 8) - S1            # "no sabes por dónde comenzar"
    def f(t):
        fr = drift(bg, t).copy()
        # tarjeta entra y, al preguntar, se aparta a la izquierda
        k = ease_out(prog(t, 0, 0.6)); m = ease_io(prog(t, t_q - 0.2, 0.7))
        cx = lerp(CX, 640, m); cy = lerp(CY + 120, CY, k); sc = lerp(1.15, 1.3, k) * lerp(1, 0.8, m)
        rot = lerp(-4, -2, k) * (1 - m) + -3 * m
        lay = Image.new("RGBA", (980, 680), (0, 0, 0, 0))
        place(lay, card, 490, 340); place(lay, head, 490, 340 - 250 + 60); place(lay, head_sq, 490, 340 - 250 + 90)
        place(lay, lic_t, 490 - 190, 340 - 210); place(lay, lic_s, 490 + 210, 340 - 205)
        place(lay, avatar, 490 - 260, 340 + 60); place(lay, av_head, 490 - 260, 340 + 30); place(lay, av_body, 490 - 260, 340 + 105)
        for i, l in enumerate(lines):
            kk = ease_out(prog(t, 0.35 + i * 0.1, 0.4))
            place(lay, crop_reveal(l, kk), 490 - 60 + l.size[0] * kk / 2, 340 - 10 + i * 52)
        s_k, s_a = pop(t, t_apr, 0.35)
        if t >= t_apr:
            place(lay, stamp_box, 490 + 170, 340 + 165, 1.6 - 0.6 * min(1, s_k), s_a, -12)
            place(lay, stamp, 490 + 170, 340 + 165, 1.6 - 0.6 * min(1, s_k), s_a, -12)
        place(fr, Sprite(lay), cx, cy, sc, clamp(k * 2), rot)
        if t >= t_q:
            a = ease_out(prog(t, t_q, 0.5))
            place(fr, q, lerp(1460, 1360, a), CY + 40, 1, a)
            for j, (dx, dy, sz) in enumerate([(-260, -250, 0.9), (180, -290, 0.6), (240, 230, 0.7)]):
                kk, aa = pop(t, t_q + 0.25 + j * 0.15)
                place(fr, qmark, 1360 + dx, CY + dy + 8 * math.sin(t * 3 + j), sz * kk, aa * 0.85, 10 * math.sin(t * 2 + j))
        return fr
    return f

# ---------------------------------------------------------------- 2. TELÉFONO
S2, E2 = wt("0154", 9), wt("0154", 21, "e") + 0.15
@scene("02_telefono", S2, E2)
def telefono():
    bg = background(2, (760, 540))
    body = rrect(380, 760, 56, hx("#0d2240"), outline=hx("#a9c0d6"), width=6, shadow=30)
    screen = rrect(340, 690, 40, hx("#1d4673"))
    notch = rrect(110, 26, 13, hx("#0d2240"))
    avatar = circle(150, SAND)
    av_i = text("C", "black", 80, NAVY)
    name = text("Cliente", "black", 46, WHITE)
    sub = text("llamada entrante…", "semi", 26, ICE)
    acc, rej = circle(100, GREEN), circle(100, RED)
    ph = draw_lines(60, 60, [[(14, 30), (46, 30)]], WHITE, 7)
    ring = circle(420, (0, 0, 0, 0), outline=hx("#e4893f", 200), width=5)
    b1 = rrect(470, 120, 40, WHITE, shadow=16); b1t = text("¿Qué le respondo?", "bold", 40, NAVY)
    b2 = rrect(300, 110, 40, ORANGE, shadow=16); b2t = text("•  •  •", "black", 44, WHITE)
    def f(t):
        fr = drift(bg, t).copy()
        k = ease_out(prog(t, 0, 0.5))
        shake = 6 * math.sin(t * 60) * (0.5 + 0.5 * math.sin(t * 6)) if t > 0.4 else 0
        px, py = 740 + shake, CY + lerp(200, 0, k)
        for j in range(3):  # ondas de timbre
            ph_t = ((t * 0.9 + j / 3) % 1)
            place(fr, ring, px, py - 120, 0.6 + ph_t * 0.9, (1 - ph_t) * 0.6 * k)
        place(fr, body, px, py, 1, k); place(fr, screen, px, py, 1, k); place(fr, notch, px, py - 325, 1, k)
        place(fr, avatar, px, py - 170, 1, k); place(fr, av_i, px, py - 172, 1, k)
        place(fr, name, px, py - 40, 1, k); place(fr, sub, px, py + 10, 1, k)
        place(fr, rej, px - 90, py + 230, 1, k); place(fr, acc, px + 90, py + 230, 1 + 0.06 * math.sin(t * 9), k)
        place(fr, ph, px - 90, py + 230, 1, k, 45); place(fr, ph, px + 90, py + 230, 1, k, -45)
        tb1 = wt("0154", 17) - S2   # "y no saben qué responder"
        kk, aa = pop(t, tb1)
        place(fr, b1, 1330, CY - 110, kk, aa); place(fr, b1t, 1330, CY - 112, kk, aa)
        kk, aa = pop(t, tb1 + 0.5)
        place(fr, b2, 1250, CY + 60, kk, aa)
        dots = "•  •  •"
        place(fr, b2t, 1250, CY + 56, kk, aa * (0.55 + 0.45 * math.sin(t * 8)))
        return fr
    return f

# ---------------------------------------------------------------- 3. COMPARACIÓN
S3, E3 = wt("0156", 0), wt("0156", 15, "e") + 0.2
@scene("03_comparacion", S3, E3)
def comparacion():
    bg = background(3, (960, 700))
    base_y, bw, gap = 860, 190, 90
    xs = [CX - 1.5 * (bw + gap) + i * (bw + gap) for i in range(4)]
    heights = [520, 600, 450, 120]
    cols = [STEEL, ICE, STEEL, ORANGE]
    bars = [rrect(bw, h, 18, c) for h, c in zip(heights, cols)]
    labels = [text(s, "bold", 34, ICE if i < 3 else ORANGE) for i, s in enumerate(["Agente A", "Agente B", "Agente C", "TÚ"])]
    axis = rrect(1240, 6, 3, hx("#a9c0d6", 120))
    title = caption_safe_title("Compararte con otros", 64)
    tag = rrect(330, 84, 42, RED); tag_t = text("ESTANCADO", "black", 40, WHITE)
    arrow_up = [poly(60, 50, [(30, 0), (60, 50), (0, 50)], WHITE) for _ in range(3)]
    flat = draw_lines(260, 40, [[(10, 20), (250, 20)]], WHITE, 8)
    t_est = wt("0156", 15) - S3  # "estancado"
    def f(t):
        fr = drift(bg, t).copy()
        a = ease_out(prog(t, 0, 0.5))
        place(fr, title, CX, 150, 1, a)
        place(fr, axis, CX, base_y + 3, 1, a)
        for i, (b, x) in enumerate(zip(bars, xs)):
            g = ease_out(prog(t, 0.3 + i * 0.18, 1.3 if i < 3 else 0.6))
            if g > 0:
                sp = crop_reveal(b, g, "y")
                place(fr, sp, x, base_y - sp.size[1] / 2, 1, 1)
            place(fr, labels[i], x, base_y + 50, 1, a)
            if i < 3 and g >= 1:
                kk, aa = pop(t, 0.3 + i * 0.18 + 1.3)
                place(fr, arrow_up[i], x, base_y - heights[i] - 45, kk, aa)
        if t >= t_est - 0.1:
            kk, aa = pop(t, t_est - 0.1)
            place(fr, flat, xs[3], base_y - heights[3] - 40, 1, aa)
            place(fr, tag, xs[3], base_y - heights[3] - 120, kk, aa, 4 * math.sin(t * 5))
            place(fr, tag_t, xs[3], base_y - heights[3] - 122, kk, aa, 4 * math.sin(t * 5))
        return fr
    return f

# ---------------------------------------------------------------- 4. BASES
S4, E4 = wt("0168", 10), wt("0168", 43, "e") + 0.25
@scene("04_bases", S4, E4)
def bases():
    bg = background(4, (960, 760))
    chipC = rrect(420, 110, 55, hx("#ffffff", 235), shadow=18); tC = text("CONTRATOS", "black", 46, NAVY)
    chipM = rrect(420, 110, 55, hx("#ffffff", 235), shadow=18); tM = text("MARKETING", "black", 46, NAVY)
    later = text("después", "semi", 30, SAND)
    strike = rrect(440, 12, 6, RED)
    brick = rrect(230, 86, 12, ORANGE, outline=hx("#c56f2a"), width=3)
    brick2 = rrect(230, 86, 12, SAND, outline=hx("#b98a55"), width=3)
    label = text("BASES SÓLIDAS", "black", 70, WHITE, shadow=True)
    t_c = wt("0168", 17) - S4; t_m = wt("0168", 23) - S4
    t_b = wt("0168", 24) - S4; t_fin = wt("0168", 38) - S4
    rows = [(5, 0), (4, 115), (5, 0)]  # ladrillos por fila, desplazamiento
    house = [(0, 260), (0, 60), (300, -150), (600, 60), (600, 260)]
    door = [(240, 260), (240, 140), (360, 140), (360, 260)]
    def f(t):
        fr = drift(bg, t).copy()
        # fase 1: lo que NO vamos a hacer todavía
        up = ease_io(prog(t, t_b - 0.2, 0.7))
        gone = ease_io(prog(t, t_fin - 0.8, 0.5))
        for j, (chip, tt, t0, x) in enumerate([(chipC, tC, 0.1, CX - 300), (chipM, tM, t_c + 0.3, CX + 300)]):
            kk, aa = pop(t, max(0, t0))
            y = lerp(380, 150, up); s = kk * lerp(1, 0.7, up)
            al = aa * lerp(1, 0.55, up) * (1 - gone)
            place(fr, chip, x, y, s, al); place(fr, tt, x, y - 2, s, al)
            st = ease_out(prog(t, (t_c if j == 0 else t_m) + 0.1, 0.3))
            if st > 0 and al > 0:
                place(fr, crop_reveal(strike, st), x - 220 * s + 220 * s * st, y, s, al)
            if up > 0: place(fr, later, x, y + 70 * s, 1, up * 0.9 * (1 - gone))
        # fase 2: ladrillos que caen y forman la base
        if t >= t_b:
            n = 0
            for r, (cnt, off) in enumerate(rows):
                for c in range(cnt):
                    t0 = t_b + 0.12 * n; n += 1
                    x = CX - 2 * 240 + c * 240 + off; y = 830 - r * 92
                    k = prog(t, t0, 0.45)
                    if k <= 0: continue
                    yy = lerp(y - 500, y, ease_in(k)) if k < 1 else y
                    place(fr, brick if (r + c) % 2 == 0 else brick2, x, yy, 1, clamp(k * 3))
            kk, aa = pop(t, t_b + 1.2)
            place(fr, label, CX, lerp(500, 150, gone), kk, aa)
        # fase 3: la casa se dibuja sobre la base (de principio a fin)
        if t >= t_fin - 0.6:
            hp = ease_io(prog(t, t_fin - 0.6, 1.6))
            ox, oy = CX - 300, 335
            pts = path_partial([(ox + x, oy + y) for x, y in house], hp)
            if len(pts) > 1:
                place(fr, draw_lines(W, H, [pts], WHITE, 12), CX, CY)
            dp = path_partial([(ox + x, oy + y) for x, y in door], ease_io(prog(t, t_fin, 1.0)))
            if len(dp) > 1:
                place(fr, draw_lines(W, H, [dp], SAND, 10), CX, CY)
        return fr
    return f

# ---------------------------------------------------------------- 5. DOS CAMINOS
S5, E5 = wt("0202", 0), wt("0202", 13, "e") + 0.3
@scene("05_caminos", S5, E5)
def caminos():
    bg = background(5, (520, 540))
    node = circle(250, SAND, outline=WHITE, width=6); nt = text("MIEDO", "black", 50, NAVY)
    up_pts = [(560, 540), (800, 540), (950, 330), (1180, 330)]
    dn_pts = [(560, 540), (800, 540), (950, 760), (1180, 760)]
    chipA = rrect(560, 130, 65, ORANGE, shadow=20); tA = text("ACTÚAN con miedo", "black", 44, WHITE)
    chipB = rrect(560, 130, 65, hx("#3a4d66"), shadow=20); tB = text("se paralizan", "bold", 44, ICE)
    resA = text("PRODUCEN  ↑", "black", 40, ORANGE); resB = text("abandonan  ↓", "bold", 36, GREY)
    banner = rrect(980, 120, 60, WHITE, shadow=24); bt = text("Eso también se aprende", "black", 54, NAVY)
    t_act = wt("0202", 5) - S5; t_apr = wt("0202", 9) - S5
    def f(t):
        fr = drift(bg, t).copy()
        kk, aa = pop(t, 0.0, 0.5)
        place(fr, node, 400, 540, kk, aa); place(fr, nt, 400, 538, kk, aa)
        pd = ease_io(prog(t, 0.6, 0.9))
        pb = path_partial(dn_pts, pd)
        if len(pb) > 1: place(fr, draw_lines(W, H, [pb], hx("#7d8ea3"), 10), CX, CY)
        if pd >= 1:
            kk2, aa2 = pop(t, 1.5)
            place(fr, chipB, 1440, 760, kk2, aa2 * 0.95); place(fr, tB, 1440, 757, kk2, aa2)
            place(fr, resB, 1440, 860, 1, aa2 * 0.8)
        pu = ease_io(prog(t, t_act - 0.4, 0.8))
        pa = path_partial(up_pts, pu)
        if len(pa) > 1: place(fr, draw_lines(W, H, [pa], ORANGE, 14), CX, CY)
        if pu >= 1:
            kk3, aa3 = pop(t, t_act + 0.4)
            place(fr, chipA, 1440, 330, kk3 * (1 + 0.02 * math.sin(t * 4)), aa3); place(fr, tA, 1440, 327, kk3, aa3)
            place(fr, resA, 1440, 445, 1, aa3)
        if t >= t_apr:
            b = ease_out(prog(t, t_apr, 0.5))
            place(fr, banner, CX, lerp(-100, 120, b), 1, b); place(fr, bt, CX, lerp(-100, 118, b), 1, b)
        return fr
    return f

# ---------------------------------------------------------------- 6. NO ES UNA PELÍCULA
S6, E6 = wt("0203", 15), wt("0203", 31, "e") + 0.25
@scene("06_pelicula", S6, E6)
def pelicula():
    bg = background(6, (960, 540))
    scr = rrect(560, 340, 26, hx("#0d2240"), outline=ICE, width=6, shadow=24)
    play = poly(120, 130, [(10, 0), (120, 65), (10, 130)], WHITE)
    pop_b = poly(200, 220, [(0, 30), (200, 30), (165, 220), (35, 220)], RED)
    stripes = draw_lines(200, 220, [[(60, 40), (75, 210)], [(140, 40), (125, 210)]], WHITE, 14, False)
    kern = [circle(60, hx("#fff3d6")) for _ in range(5)]
    lbl1 = text("Una película", "black", 54, WHITE)
    bigx = cross_mark(380, RED, 30)
    book = rrect(420, 520, 22, WHITE, shadow=24)
    spine = rrect(30, 520, 0, ORANGE)
    rule = [rrect(300, 8, 4, hx("#c9d6e3")) for _ in range(7)]
    pen = poly(60, 340, [(15, 0), (45, 0), (45, 280), (30, 340), (15, 280)], SAND)
    lbl2 = text("Un curso con calma", "black", 54, ORANGE)
    chk = check_mark(150, GREEN, 22)
    t_x = wt("0203", 24, "e") - S6; t_c = wt("0203", 25) - S6
    def f(t):
        fr = drift(bg, t).copy()
        k = ease_out(prog(t, 0, 0.5))
        xk = ease_out(prog(t, t_x, 0.35)) if t >= t_x else 0
        ka = k * lerp(1, 0.4, xk)
        lx = 560
        place(fr, scr, lx, 430, k, ka); place(fr, play, lx + 10, 430, k, ka)
        place(fr, pop_b, lx + 240, 640, k, ka); place(fr, stripes, lx + 240, 640, k, ka)
        for j, (dx, dy) in enumerate([(-50, -100), (0, -120), (50, -95), (-20, -80), (30, -75)]):
            place(fr, kern[j], lx + 240 + dx, 640 + dy + 4 * math.sin(t * 4 + j), k, ka)
        place(fr, lbl1, lx, 790, 1, ka)
        if xk > 0:
            place(fr, bigx, lx, 480, lerp(1.4, 1, xk), xk)
        if t >= t_c:
            b = ease_out(prog(t, t_c, 0.6)); rx = lerp(1700, 1380, b)
            place(fr, book, rx, 470, 1, b); place(fr, spine, rx - 195, 470, 1, b)
            for j, r in enumerate(rule):
                rk = ease_out(prog(t, t_c + 0.3 + j * 0.08, 0.3))
                place(fr, crop_reveal(r, rk), rx - 150 + 150 * rk + 20, 300 + j * 55, 1, b)
            place(fr, pen, rx + 230, 520, 1, b, -20 + 6 * math.sin(t * 5))
            place(fr, lbl2, 1380, 790, 1, b)
            kk, aa = pop(t, t_c + 0.8)
            place(fr, chk, rx + 150, 260, kk, aa)
        return fr
    return f

# ---------------------------------------------------------------- 7. PASO A PASO
S7, E7 = wt("0213", 17), wt("0213", 28, "e") + 0.4
@scene("07_escalera", S7, E7)
def escalera():
    bg = background(7, (1300, 300))
    n = 7
    stepw, steph = 200, 95
    x0, y0 = 330, 960
    step = rrect(stepw, 0 + 10, 4, WHITE)
    blocks = [rrect(stepw - 8, steph * (i + 1), 10, ORANGE if i == n - 1 else (STEEL if i % 2 else hx("#4f7898"))) for i in range(n)]
    flag_pole = rrect(10, 150, 5, WHITE)
    flag = poly(110, 70, [(0, 0), (110, 35), (0, 70)], ORANGE)
    dot = circle(46, WHITE)
    words = [("paso a paso", wt("0213", 19) - S7), ("repetidos", wt("0213", 26) - S7), ("constantes", wt("0213", 28) - S7)]
    wsp = [text(w, "black", 64, ORANGE if i == 2 else WHITE, shadow=True) for i, (w, _) in enumerate(words)]
    def f(t):
        fr = drift(bg, t).copy()
        span = max(1.0, (E7 - S7) - 1.2)
        for i in range(n):
            t0 = 0.15 + i * span / n
            k = ease_out(prog(t, t0, 0.4))
            if k <= 0: continue
            sp = crop_reveal(blocks[i], k, "y")
            x = x0 + i * stepw
            place(fr, sp, x, y0 - sp.size[1] / 2, 1, 1)
        # el punto salta al escalón recién aparecido
        t0s = [0.15 + i * span / n for i in range(n)]
        i = max([j for j in range(n) if t >= t0s[j] + 0.1] or [0])
        p = ease_io(prog(t, t0s[i] + 0.1, 0.35)) if i > 0 else 1
        top = lambda j: y0 - steph * (j + 1) - 23
        xx = lerp(x0 + (i - 1) * stepw, x0 + i * stepw, p) if i > 0 else x0
        yy = (lerp(top(i - 1), top(i), p) if i > 0 else top(0)) - math.sin(math.pi * p) * 70 * (i > 0)
        place(fr, dot, xx, yy, 1, ease_out(prog(t, 0.2, 0.3)))
        if t > 0.15 + span:
            fk = ease_out(prog(t, 0.15 + span, 0.5))
            fx, fy = x0 + (n - 1) * stepw, y0 - steph * n
            place(fr, flag_pole, fx, fy - 75, 1, fk); place(fr, flag, fx + 55, fy - 115, fk, fk)
        for j, ((w, t0), sp) in enumerate(zip(words, wsp)):
            kk, aa = pop(t, max(0, t0 - 0.1))
            place(fr, sp, 480 + j * 20, 220 + j * 95, kk, aa)
        return fr
    return f

# ---------------------------------------------------------------- 8. CIERRE (placa final)
@scene("08_cierre", 0, 7.0, outro=True)
def cierre():
    bg = background(8, (560, 540))
    logo_sp = logo(330)
    ring = circle(520, (0, 0, 0, 0), outline=hx("#e4893f", 180), width=5)
    pill = rrect(420, 70, 35, ORANGE); pt = text("PRÓXIMA CLASE", "black", 34, WHITE)
    t1 = text("Verdades y mitos", "black", 92, WHITE, shadow=True)
    t2 = text("del Real Estate", "black", 92, ORANGE, shadow=True)
    line = rrect(640, 6, 3, hx("#a9c0d6", 150))
    url = text("Ramon Academy", "semi", 38, ICE)
    def f(t):
        fr = drift(bg, t).copy()
        k = ease_out(prog(t, 0.1, 0.8))
        place(fr, ring, 560, 540, lerp(0.7, 1, k) + 0.02 * math.sin(t * 2), k * 0.8)
        place(fr, logo_sp, 560, 540, lerp(0.85, 1, back(prog(t, 0.2, 0.7))), k)
        kk, aa = pop(t, 0.7); place(fr, pill, 1290, 330, kk, aa); place(fr, pt, 1290, 328, kk, aa)
        for j, sp in enumerate([t1, t2]):
            a = ease_out(prog(t, 1.0 + j * 0.25, 0.6))
            place(fr, sp, lerp(1380, 1290, a), 450 + j * 110, 1, a)
        lk = ease_out(prog(t, 1.6, 0.6))
        place(fr, crop_reveal(line, lk), 1290 - 320 + 320 * lk, 650, 1, lk)
        place(fr, url, 1290, 710, 1, ease_out(prog(t, 1.9, 0.6)))
        return fr
    return f
