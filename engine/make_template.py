"""Extrae una plantilla mínima y ANÓNIMA de un borrador real de CapCut Desktop.

CapCut no documenta su formato; la forma fiable de generar borradores que abra tu versión
es clonar objetos de un borrador que ella misma guardó. Este script toma, de un borrador
existente, solo las piezas que usa build_draft.py (un segmento de video, de imagen, de texto,
de audio, un keyframe y sus materiales auxiliares), borra rutas, nombres e identificadores
del equipo, y lo guarda en template/capcut_template.json.

Uso:
  python engine/make_template.py "<carpeta de un borrador de CapCut>"
El borrador debe tener: un clip de video, una imagen, un texto, un audio y al menos un keyframe.
"""
import json, os, re, sys, copy

SENSITIVE_KEYS = {"device_id", "hard_disk_id", "mac_address", "file_Path", "draft_fold_path", "draft_root_path",
                  "draft_json_file", "draft_cover", "path", "media_path", "extra_info", "material_name", "name",
                  "draft_name", "local_material_id", "music_id", "unique_id", "cloud_draft_cover"}
ID_RE = re.compile(r"^[0-9a-fA-F-]{16,}$")

def scrub(o, keep_font=True):
    if isinstance(o, dict):
        out = {}
        for k, v in o.items():
            if k in SENSITIVE_KEYS and isinstance(v, str):
                out[k] = v if (keep_font and k == "path" and is_system_font(v)) else ""
            else:
                out[k] = scrub(v, keep_font)
        return out
    if isinstance(o, list): return [scrub(x, keep_font) for x in o]
    if isinstance(o, str) and re.search(r"[A-Za-z]:[\\/]|\\Users\\|/Users/", o) and not is_system_font(o):
        return ""
    return o

def is_system_font(p):
    p = p.lower()
    return p.startswith(("c:/windows/fonts", "/system/library/fonts", "/library/fonts"))

def load_draft(src):
    """El archivo principal cambia según sistema y versión: draft_content.json (Windows), draft_info.json (Mac),
    o dentro de Timelines/<id>/. Devuelve el primero que sea JSON legible."""
    cands = []
    pj = os.path.join(src, "Timelines", "project.json")
    if os.path.exists(pj):
        try:
            tid = json.load(open(pj, encoding="utf-8")).get("main_timeline_id")
            if tid: cands += [os.path.join(src, "Timelines", tid, n) for n in ("draft_content.json", "draft_info.json", "template-2.tmp")]
        except ValueError:
            pass
    cands += [os.path.join(src, n) for n in ("draft_content.json", "draft_info.json", "template-2.tmp")]
    seen_encrypted = False
    for c in cands:
        if not os.path.exists(c): continue
        try:
            d = json.load(open(c, encoding="utf-8"))
            if isinstance(d, dict) and "tracks" in d and "materials" in d: return d
        except (ValueError, UnicodeDecodeError):
            seen_encrypted = True
    sys.exit("No encuentro un borrador legible en esa carpeta." + (
        " Los archivos parecen cifrados: esta versión de CapCut guarda los borradores cifrados y el editor no puede leerlos." if seen_encrypted else ""))

def main(src):
    d = load_draft(src)
    meta = json.load(open(os.path.join(src, "draft_meta_info.json"), encoding="utf-8"))
    idx = {o["id"]: (k, o) for k, v in d["materials"].items() if isinstance(v, list) for o in v if isinstance(o, dict) and "id" in o}
    vsegs = [s for t in d["tracks"] if t["type"] == "video" for s in t["segments"]]
    main_seg = next(s for s in vsegs if idx[s["material_id"]][1]["type"] == "video")
    photo_seg = next(s for s in vsegs if idx[s["material_id"]][1]["type"] == "photo")
    text_seg = next(t for t in d["tracks"] if t["type"] == "text")["segments"][0]
    audio_seg = next(t for t in d["tracks"] if t["type"] == "audio")["segments"][0]
    kf = next(s for t in d["tracks"] for s in t["segments"] if s.get("common_keyframes"))["common_keyframes"][0]
    kf = dict(kf, keyframe_list=kf["keyframe_list"][:1])
    extras = {}
    for s in (main_seg, photo_seg, text_seg, audio_seg):
        for r in s["extra_material_refs"]:
            cat, obj = idx[r]
            if cat != "transitions": extras[r] = [cat, obj]
    skeleton = {k: v for k, v in d.items() if k not in ("tracks", "materials")}
    skeleton["platform"] = dict(skeleton.get("platform") or {}, device_id="", hard_disk_id="", mac_address="")
    skeleton["last_modified_platform"] = dict(skeleton.get("last_modified_platform") or {}, device_id="", hard_disk_id="", mac_address="")
    root_path = os.path.join(os.path.dirname(src), "root_meta_info.json")
    root_entry = None
    if os.path.exists(root_path):
        r = json.load(open(root_path, encoding="utf-8"))
        root_entry = (r.get("all_draft_store") or [None])[0]
    m = copy.deepcopy(meta)
    for g in m.get("draft_materials", []):
        g["value"] = g["value"][:1] if g.get("type") == 0 else []
    tpl = {
        "_info": "Plantilla anónima extraída de un borrador de CapCut Desktop. Regenerar con engine/make_template.py si tu versión de CapCut no abre los proyectos.",
        "capcut_version": d.get("last_modified_platform", {}).get("app_version") or d.get("new_version"),
        "materials_shape": {k: ([] if isinstance(v, list) else v) for k, v in d["materials"].items()},
        "skeleton": skeleton, "meta": m, "root_entry": root_entry,
        "video_mat": idx[main_seg["material_id"]][1], "photo_mat": idx[photo_seg["material_id"]][1],
        "text_mat": idx[text_seg["material_id"]][1], "audio_mat": idx[audio_seg["material_id"]][1],
        "main_seg": main_seg, "photo_seg": photo_seg, "text_seg": text_seg, "audio_seg": audio_seg,
        "keyframe": kf, "extras": extras,
    }
    tpl = scrub(tpl)
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "template", "capcut_template.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(tpl, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Plantilla guardada en {out} (CapCut {tpl['capcut_version']})")

if __name__ == "__main__":
    main(sys.argv[1])
