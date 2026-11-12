"""Paso 9 · Genera el borrador EDITABLE de CapCut Desktop (16:9, 30 fps) y lo registra en la lista de proyectos.
Pistas: Ramón (cortes + reencuadres) · tarjetas · rótulos · tomas de apoyo · logo · subtítulos (texto editable)
· música · efectos. Clona objetos de template/capcut_template.json (extraído de un borrador real de CapCut).
Cierra CapCut antes de ejecutarlo (CapCut reescribe la lista de proyectos al cerrarse).
"""
import json, os, sys, uuid, time, copy, shutil, subprocess, re
from common import project_from_argv, REPO
from timeline import Timeline

P = project_from_argv(); C = P.cfg; TL = Timeline(P)
NAME = C["name"]
DRAFTS = C.get("capcut_drafts_dir") or os.path.expandvars(r"%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft")
DRAFTS = DRAFTS.replace("\\", "/"); OUT = f"{DRAFTS}/{NAME}"
PD = P.dir.replace("\\", "/")
MEDIA, BROLL, OVL, AUD = (f"{PD}/{d}" for d in ("media", "broll", "overlays", "audio"))
US, W, H = 1_000_000, 1920, 1080
FONTS = P.brand.get("fonts", {})
FONT_CAP = FONTS.get("black", "C:/Windows/Fonts/seguibl.ttf")
def rgb(h): return [round(int(h[i:i + 2], 16) / 255, 4) for i in (1, 3, 5)]
COL = P.brand["colors"]
WHITE, ACCENT, DEEP = [1, 1, 1], rgb(COL.get("accent", "#e4893f")), rgb(COL.get("deep", "#0a1d36"))

TPL = json.load(open(os.path.join(REPO, "template", "capcut_template.json"), encoding="utf-8"))
clone = copy.deepcopy
def hexid(): return uuid.uuid4().hex
def UUID(): return str(uuid.uuid4()).upper()
def us(s): return int(round(s * US))
NOW = int(time.time())

materials = clone(TPL["materials_shape"])
for k, v in materials.items():
    if isinstance(v, list): materials[k] = []
tracks, meta_materials = [], []
tMain, tPhoto, tTextSeg, tAudioSeg = TPL["main_seg"], TPL["photo_seg"], TPL["text_seg"], TPL["audio_seg"]
tKf = TPL["keyframe"]

def extras(tseg, skip=("transitions",)):
    refs = []
    for r in tseg["extra_material_refs"]:
        if r not in TPL["extras"]: continue
        cat, obj = TPL["extras"][r]
        if cat in skip: continue
        c = clone(obj); c["id"] = UUID() if ("-" in r and re.search("[A-F]", r)) else hexid()
        materials.setdefault(cat, []).append(c); refs.append(c["id"])
    return refs

def kf(ptype, points):
    k = clone(tKf); k["id"] = hexid(); k["property_type"] = ptype
    base = tKf["keyframe_list"][0]
    k["keyframe_list"] = [dict(clone(base), id=hexid(), time_offset=us(t), values=[v]) for t, v in points]
    return k

def seg(tseg, mid, start, dur, src, refs, render_idx, track_idx):
    s = clone(tseg)
    s.update(id=hexid(), material_id=mid, extra_material_refs=refs, common_keyframes=[], keyframe_refs=[],
             target_timerange={"start": us(start), "duration": us(dur)},
             source_timerange=None if src is None else {"start": us(src), "duration": us(dur)},
             render_index=render_idx, track_render_index=track_idx, visible=True)
    return s

def track(ttype, name, segments):
    segments.sort(key=lambda s: s["target_timerange"]["start"])
    tracks.append({"id": hexid(), "type": ttype, "segments": segments, "flag": 0, "attribute": 0, "name": name, "is_default_name": False})

def meta_entry(path, mtype, dur, w, h):
    mid = str(uuid.uuid4())
    vals = TPL["meta"]["draft_materials"][0]["value"]
    e = clone(vals[0]) if vals else {}
    e.update(id=mid, file_Path=path, extra_info=path.split("/")[-1], metetype=mtype, duration=us(dur), width=w, height=h,
             roughcut_time_range={"duration": -1, "start": -1} if mtype == "photo" else {"duration": us(dur), "start": 0},
             create_time=NOW, import_time=NOW, import_time_ms=NOW * US)
    meta_materials.append(e); return mid

def probe(path):
    o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height,codec_type", "-of", "json", path], capture_output=True, text=True).stdout
    j = json.loads(o); v = next((s for s in j["streams"] if s["codec_type"] == "video"), {})
    return float(j["format"]["duration"]), v.get("width", 0), v.get("height", 0)

_vc, _pc, _ac = {}, {}, {}
def video_mat(path):
    if path not in _vc:
        dur, w, h = probe(path)
        m = clone(TPL["video_mat"]); m.update(id=hexid(), path=path, material_name=path.split("/")[-1], duration=us(dur), width=w, height=h,
                                             local_material_id=meta_entry(path, "video", dur, w, h))
        m["material_id"] = m["id"]; materials["videos"].append(m); _vc[path] = (m["id"], dur)
    return _vc[path]
def photo_mat(path):
    if path not in _pc:
        m = clone(TPL["photo_mat"]); m.update(id=hexid(), path=path, material_name=path.split("/")[-1], width=W, height=H, duration=10_800_000_000,
                                             local_material_id=meta_entry(path, "photo", 5, W, H))
        materials["videos"].append(m); _pc[path] = m["id"]
    return _pc[path]
def audio_mat(path):
    if path not in _ac:
        dur = probe(path)[0]
        a = clone(TPL["audio_mat"]); a.update(id=hexid(), unique_id=hexid(), name=path.split("/")[-1], path=path, duration=us(dur), music_id=hexid(),
                                             local_material_id=meta_entry(path, "music", dur, 0, 0))
        materials["audios"].append(a); _ac[path] = (a["id"], dur)
    return _ac[path]

def text_mat(parts, size, stroke=None, shadow=True, align=1, max_w=0.82):
    txt, styles = "", []
    for p, color, fnt in parts:
        st = {"fill": {"alpha": 1, "content": {"render_type": "solid", "solid": {"alpha": 1, "color": color}}},
              "range": [len(txt), len(txt) + len(p)], "size": size, "bold": False, "italic": False, "underline": False,
              "strokes": [], "font": {"id": "", "path": fnt}}
        if stroke: st["strokes"] = [{"content": {"render_type": "solid", "solid": {"alpha": 1, "color": stroke[0]}}, "width": stroke[1]}]
        styles.append(st); txt += p
    m = clone(TPL["text_mat"])
    m.update(id=hexid(), content=json.dumps({"text": txt, "styles": styles}, ensure_ascii=False), font_path=parts[0][2], font_size=size,
             alignment=align, has_shadow=shadow, shadow_color="#000000", shadow_alpha=0.5, shadow_smoothing=1.8, shadow_distance=4,
             shadow_angle=-60, border_color=COL.get("deep", "#0a1d36") if stroke else "", border_width=stroke[1] if stroke else 0.06,
             border_alpha=1, line_max_width=max_w, line_spacing=0.02, background_alpha=0, background_color="")
    materials["texts"].append(m); return m["id"]

def fade(d, delay=0.0, fin=0.25, fout=0.3):
    return kf("KFTypeAlpha", [(0, 0)] + ([(delay, 0)] if delay > 0 else []) + [(delay + fin, 1), (max(delay + fin, d - fout), 1), (d, 0)])
def slide_in(d, x, dx, delay=0.0):
    return [kf("KFTypePositionX", [(delay, x + dx), (delay + 0.45, x), (max(delay + 0.45, d - 0.35), x), (d, x + dx * 0.5)]), fade(d, delay, 0.3, 0.35)]
def pop(d, delay=0.0, frm=0.85):
    return [kf("KFTypeScaleX", [(delay, frm), (delay + 0.16, 1.05), (delay + 0.3, 1)]),
            kf("KFTypeScaleY", [(delay, frm), (delay + 0.16, 1.05), (delay + 0.3, 1)]), fade(d, delay, 0.12, 0.12)]

TOTAL = TL.total
def load_json(p, default): return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default
OV = load_json(f"{OVL}/overlays.json", {"groups": []})
BR = load_json(f"{BROLL}/broll.json", {})
OUTRO_NAME = next((k for k, v in BR.items() if v.get("outro")), None)
OUTRO = BR[OUTRO_NAME]["dur"] if OUTRO_NAME else 0.0
END = TOTAL + OUTRO
groups = sorted(OV["groups"], key=lambda g: g["start"])
for a, b in zip(groups, groups[1:]): a["end"] = min(a["end"], b["start"] - 0.05)
def card_side(t):
    for g in groups:
        if g["start"] - 0.2 <= t <= g["end"] + 0.2: return g["side"]
    return None

# ---------- 1. pista principal: cortes con reencuadre alterno ----------
FR = C.get("framing", {})
EYES_Y, FACE_X = FR.get("eyes_y", 0.36), FR.get("face_x", -0.08)     # posición de ojos/cara en unidades de medio lienzo
TARGET_Y = FR.get("target_y", 0.33); CYCLE = FR.get("cycle", [1.0, 1.32, 1.0, 1.55])
def framing(s, side=None):
    if side:
        return s, (0.09 if side == "L" else -0.09) * (s > 1), -0.03 * (s > 1)
    y = max(TARGET_Y - EYES_Y * s, -(s - 1)); x = max(min(-FACE_X * s, s - 1), -(s - 1))
    return s, round(x, 4), round(y, 4)
main = []
for n, e in enumerate(TL.edl):
    vid, _ = video_mat(f"{MEDIA}/{e['clip']}.mp4")
    s = seg(tMain, vid, e["t"], e["b"] - e["a"], e["a"], extras(tMain), 0, 0)
    s["volume"] = s["last_nonzero_volume"] = C.get("voice_volume", 1.0)
    side = card_side(e["t"] + 0.1)
    z = (1.0 if n % 2 else 1.08) if side else CYCLE[n % len(CYCLE)]
    z, x, y = framing(z, side)
    s["clip"] = dict(s["clip"], scale={"x": z, "y": z}, transform={"x": x, "y": y})
    main.append(s)
if OUTRO_NAME:
    cid, _ = video_mat(f"{BROLL}/{OUTRO_NAME}.mp4")
    s = seg(tMain, cid, TOTAL, OUTRO, 0, extras(tMain), 0, 0); s["volume"] = 0
    s["clip"] = dict(s["clip"], scale={"x": 1, "y": 1}, transform={"x": 0, "y": 0})
    s["common_keyframes"] = [kf("KFTypeAlpha", [(0, 0), (0.4, 1), (OUTRO - 0.5, 1), (OUTRO, 0)])]
    main.append(s)
track("video", "Principal (cortes)", main)

TI = [1]
def next_ti(): TI[0] += 1; return TI[0]
def photo_track(name, items):
    if not items: return
    ti = next_ti(); segs = []
    for it in items:
        s = seg(tPhoto, photo_mat(it["path"]), it["start"], it["dur"], 0, extras(tPhoto), ti, ti)
        s["clip"] = dict(s["clip"], alpha=1, scale={"x": 1, "y": 1}, transform={"x": 0, "y": 0}); s["common_keyframes"] = it.get("kfs", [])
        segs.append(s)
    track("video", name, segs)

# ---------- 2. tarjetas ----------
panels, statements, rows, pops_t = [], [], [[] for _ in range(8)], []
for g in groups:
    st, en = g["start"], g["end"]; d = en - st; dx = -0.12 if g["side"] == "L" else 0.12
    panels.append({"path": f"{OVL}/{g['panel']}", "start": st, "dur": d, "kfs": slide_in(d, 0, dx)}); pops_t.append(st)
    if g.get("statement"):
        statements.append({"path": f"{OVL}/{g['statement']}", "start": st + 0.25, "dur": d - 0.25, "kfs": slide_in(d - 0.25, 0, dx * 0.4)})
    for k, it in enumerate(g["items"]):
        t0 = min(max(st + 0.35, it["t"] - 0.1), en - 0.6)
        rows[k].append({"path": f"{OVL}/{it['file']}", "start": t0, "dur": en - t0, "kfs": slide_in(en - t0, 0, dx * 0.3)}); pops_t.append(t0)
photo_track("Tarjetas · panel", panels); photo_track("Tarjetas · frase", statements)
for k, r in enumerate(rows): photo_track(f"Tarjetas · punto {k + 1}", r)

# ---------- 3. rótulos ----------
if "lower_name" in OV:
    ln = OV["lower_name"]; d = ln["end"] - ln["start"]
    photo_track("Rótulo nombre", [{"path": f"{OVL}/lower_name.png", "start": ln["start"], "dur": d, "kfs": slide_in(d, 0, -0.25)}])
if "title_pill" in OV:
    tp = OV["title_pill"]; d = tp["end"] - tp["start"]
    photo_track("Título", [{"path": f"{OVL}/title_pill.png", "start": tp["start"], "dur": d, "kfs": pop(d, 0, 0.7)}])

# ---------- 4. tomas de apoyo ----------
ti = next_ti(); brs, whooshes = [], []
for name, b in sorted(BR.items(), key=lambda kv: kv[1]["start"]):
    if b.get("outro"): continue
    vid, dur = video_mat(f"{BROLL}/{name}.mp4"); d = min(b["dur"], dur)
    s = seg(tMain, vid, b["start"], d, 0, extras(tMain), ti, ti); s["volume"] = s["last_nonzero_volume"] = 0
    s["clip"] = dict(s["clip"], scale={"x": 1, "y": 1}, transform={"x": 0, "y": 0})
    s["common_keyframes"] = [kf("KFTypeAlpha", [(0, 0), (0.2, 1), (d - 0.2, 1), (d, 0)]),
                             kf("KFTypeScaleX", [(0, 1.06), (0.35, 1.0), (d, 1.02)]), kf("KFTypeScaleY", [(0, 1.06), (0.35, 1.0), (d, 1.02)])]
    brs.append(s); whooshes += [(b["start"] - 0.3, "in"), (b["start"] + d - 0.25, "out")]
if brs: track("video", "Tomas de apoyo (motion graphics)", brs)

# ---------- 5. logo ----------
if OV.get("logo_bug"):
    photo_track("Logo", [{"path": f"{OVL}/logo_bug.png", "start": 0.5, "dur": TOTAL - 0.5, "kfs": [fade(TOTAL - 0.5, 0, 0.6, 0.6)]}])

# ---------- 6. subtítulos dinámicos (texto editable) ----------
CAP = C.get("captions", {})
if CAP.get("enabled", True):
    KEY = {k.lower() for k in C.get("keywords", [])}
    words = TL.words(); chunks, cur = [], []
    maxw, maxc = CAP.get("max_words", 4), CAP.get("max_chars", 22)
    for i, w in enumerate(words):
        cur.append(w); txt = " ".join(x["w"] for x in cur); nxt = words[i + 1] if i + 1 < len(words) else None
        if (len(cur) >= maxw or len(txt) >= maxc or w["w"][-1:] in ".,?!:;" or nxt is None or nxt["s"] - w["e"] > 0.35
                or len(txt) + len(nxt["w"]) > maxc + 4):
            chunks.append(cur); cur = []
    ti = next_ti(); caps = []
    for k, ch in enumerate(chunks):
        st = ch[0]["s"]; en = chunks[k + 1][0]["s"] if k + 1 < len(chunks) else ch[-1]["e"] + 0.4
        en = max(min(en, ch[-1]["e"] + 0.6, TOTAL), st + 0.2)
        parts = []
        for j, w in enumerate(ch):
            bare = re.sub(r"[^\wáéíóúñü]", "", w["w"].lower())
            parts.append((w["w"].strip() + (" " if j < len(ch) - 1 else ""), ACCENT if bare in KEY else WHITE, FONT_CAP))
        if k == 0 or chunks[k - 1][-1]["w"][-1:] in ".?!":
            parts[0] = (parts[0][0][:1].upper() + parts[0][0][1:],) + parts[0][1:]
        s = seg(tTextSeg, text_mat(parts, CAP.get("size", 7.5), stroke=(DEEP, 0.09)), st, en - st, None, [], 14000 + ti, ti)
        s["clip"] = dict(s["clip"], transform={"x": 0, "y": CAP.get("y", -0.80)}, scale={"x": 1, "y": 1})
        s["common_keyframes"] = [kf("KFTypeScaleX", [(0, 0.88), (0.1, 1.04), (0.18, 1)]), kf("KFTypeScaleY", [(0, 0.88), (0.1, 1.04), (0.18, 1)])]
        caps.append(s)
    track("text", "Subtítulos", caps)

# ---------- 7. audio ----------
def db(x): return round(10 ** (x / 20), 4)
def audio_track(name, items):
    items = [it for it in items if os.path.exists(it["path"])]
    if not items: return
    ti = next_ti(); segs = []
    for it in items:
        aid, adur = audio_mat(it["path"]); d = min(it.get("dur", adur), adur)
        refs = extras(tAudioSeg, ())
        if it.get("fade"):
            f = {"id": hexid(), "type": "audio_fade", "fade_type": 0, "fade_in_duration": us(it["fade"][0]), "fade_out_duration": us(it["fade"][1])}
            materials.setdefault("audio_fades", []).append(f); refs.append(f["id"])
        s = seg(tAudioSeg, aid, max(0, it["start"]), d, 0, refs, 0, ti); s["volume"] = s["last_nonzero_volume"] = it["vol"]
        segs.append(s)
    track("audio", name, segs)
MIX = C.get("mix", {})
audio_track("Música (original)", [{"path": f"{AUD}/musica_fondo.wav", "start": 0, "dur": TOTAL + 0.5, "vol": db(MIX.get("music_db", -21)), "fade": (1.5, 2.0)}])
if OUTRO_NAME:
    audio_track("Música cierre", [{"path": f"{AUD}/musica_cierre.wav", "start": TOTAL - 0.3, "dur": OUTRO + 0.3, "vol": db(MIX.get("outro_db", -8)), "fade": (0.6, 2.0)}])
audio_track("Efectos · whoosh", [{"path": f"{AUD}/sfx_whoosh.wav" if k == "in" else f"{AUD}/sfx_whoosh_out.wav", "start": t, "vol": db(MIX.get("whoosh_db", -12))} for t, k in whooshes])
pops = []
for t in sorted(pops_t):
    if not pops or t - pops[-1] > 0.25: pops.append(t)
audio_track("Efectos · pop", [{"path": f"{AUD}/sfx_pop.wav", "start": t, "vol": db(MIX.get("pop_db", -17))} for t in pops])
if OUTRO_NAME:
    audio_track("Efectos · cierre", [{"path": f"{AUD}/sfx_ding.wav", "start": TOTAL + 0.6, "vol": db(MIX.get("ding_db", -12))}])

# ---------- ensamblado y registro en CapCut ----------
draft = clone(TPL["skeleton"]); DID = UUID()
draft.update(id=DID, name=NAME, duration=us(END), fps=30.0, create_time=NOW, update_time=NOW,
             canvas_config=dict(draft.get("canvas_config", {}), ratio="16:9", width=W, height=H),
             materials=materials, tracks=tracks, relationships=[], group_container=None, time_marks=None)
draft["keyframes"] = {k: [] for k in (draft.get("keyframes") or {"videos": [], "audios": [], "texts": [], "stickers": [], "effects": [], "filters": [], "adjusts": [], "handwrites": []})}
if os.path.exists(OUT): shutil.rmtree(OUT)
os.makedirs(f"{OUT}/Timelines/{DID}", exist_ok=True)
js = json.dumps(draft, ensure_ascii=False)
for p in (f"{OUT}/draft_content.json", f"{OUT}/Timelines/{DID}/draft_content.json"): open(p, "w", encoding="utf-8").write(js)
now_us = int(time.time() * US)
json.dump({"config": {"color_space": -1, "hdr_vivid": False, "mixed_track_mode_on": False, "render_index_track_mode_on": False, "use_float_render": False},
           "create_time": now_us, "id": UUID(), "main_timeline_id": DID,
           "timelines": [{"create_time": now_us, "id": DID, "is_marked_delete": False, "name": "Línea de tiempo 01", "update_time": now_us}],
           "update_time": now_us, "version": 0}, open(f"{OUT}/Timelines/project.json", "w", encoding="utf-8"), ensure_ascii=False)
MID = UUID(); m = clone(TPL["meta"])
size = sum(os.path.getsize(p) for p in {e["file_Path"] for e in meta_materials})
m.update(draft_fold_path=OUT, draft_id=MID, draft_name=NAME, draft_root_path=DRAFTS, tm_draft_create=now_us, tm_draft_modified=now_us,
         tm_duration=us(END), draft_timeline_materials_size_=size)
m["draft_materials"] = [dict(g, value=meta_materials if g.get("type") == 0 else []) for g in m["draft_materials"]]
json.dump(m, open(f"{OUT}/draft_meta_info.json", "w", encoding="utf-8"), ensure_ascii=False)
cover_src = f"{BROLL}/{OUTRO_NAME}.mp4" if OUTRO_NAME else f"{MEDIA}/{TL.edl[0]['clip']}.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "2.5", "-i", cover_src, "-frames:v", "1", "-vf", "scale=640:-2", f"{OUT}/draft_cover.jpg"])
rp = f"{DRAFTS}/root_meta_info.json"
root = json.load(open(rp, encoding="utf-8")) if os.path.exists(rp) else {"all_draft_store": [], "draft_ids": 0, "root_path": DRAFTS}
if os.path.exists(rp) and not os.path.exists(rp + ".bak_claude"): shutil.copy(rp, rp + ".bak_claude")
entry = clone(root["all_draft_store"][0] if root["all_draft_store"] else TPL["root_entry"] or {})
entry.update(draft_cover=f"{OUT}/draft_cover.jpg".replace("/", "\\"), draft_fold_path=OUT, draft_id=MID,
             draft_json_file=f"{OUT}/draft_content.json".replace("/", "\\"), draft_name=NAME, draft_root_path=DRAFTS,
             draft_timeline_materials_size=size, tm_draft_create=now_us, tm_draft_modified=now_us, tm_duration=us(END))
root["all_draft_store"] = [entry] + [d for d in root["all_draft_store"] if d.get("draft_name") != NAME]
root["draft_ids"] = len(root["all_draft_store"])
json.dump(root, open(rp, "w", encoding="utf-8"), ensure_ascii=False)
print(f"OK '{NAME}': {END:.1f}s · {len(TL.edl)} cortes · {len(brs)} tomas de apoyo · {len(groups)} tarjetas · {len(tracks)} pistas -> {OUT}")
