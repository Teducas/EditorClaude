"""Paso 10 · Valida el borrador generado: referencias rotas, solapes en una misma pista, huecos en la
pista principal, keyframes fuera de su segmento, rangos de fuente imposibles y archivos que faltan."""
import json, os, sys, collections
from common import project_from_argv

def validate(path):
    d = json.load(open(path, encoding="utf-8"))
    ids = {o["id"]: k for k, v in d["materials"].items() if isinstance(v, list) for o in v if isinstance(o, dict) and "id" in o}
    errs, missing = [], {m["path"] for k in ("videos", "audios") for m in d["materials"][k] if m.get("path") and not os.path.exists(m["path"])}
    for t in d["tracks"]:
        prev = -1
        for s in sorted(t["segments"], key=lambda s: s["target_timerange"]["start"]):
            if s["material_id"] not in ids: errs.append(f"{t['name']}: material inexistente")
            errs += [f"{t['name']}: referencia rota" for r in s["extra_material_refs"] if r not in ids]
            st, du = s["target_timerange"]["start"], s["target_timerange"]["duration"]
            if du <= 0: errs.append(f"{t['name']}: duración nula en {st / 1e6:.2f}s")
            if st < prev - 1000: errs.append(f"{t['name']}: solape en {st / 1e6:.2f}s")
            prev = st + du
            sr = s.get("source_timerange")
            if sr and ids.get(s["material_id"]) in ("videos", "audios"):
                m = next(x for x in d["materials"][ids[s["material_id"]]] if x["id"] == s["material_id"])
                if m.get("type") != "photo" and sr["start"] + sr["duration"] > m["duration"] + 1000:
                    errs.append(f"{t['name']}: la fuente pasa del final del archivo en {st / 1e6:.2f}s")
            for k in s.get("common_keyframes", []):
                if any(p["time_offset"] < 0 or p["time_offset"] > du + 1000 for p in k["keyframe_list"]):
                    errs.append(f"{t['name']}: keyframe fuera del segmento en {st / 1e6:.2f}s")
    main = sorted(d["tracks"][0]["segments"], key=lambda s: s["target_timerange"]["start"])
    gaps = [((a["target_timerange"]["start"] + a["target_timerange"]["duration"]) / 1e6) for a, b in zip(main, main[1:])
            if abs(b["target_timerange"]["start"] - a["target_timerange"]["start"] - a["target_timerange"]["duration"]) > 1000]
    print("pistas:", ", ".join(f"{t['name']} ({len(t['segments'])})" for t in d["tracks"]))
    print(f"duración: {d['duration'] / 1e6:.1f}s")
    for e in collections.Counter(errs): print("ERROR", e)
    for f in missing: print("FALTA", f)
    for g in gaps: print("HUECO en la pista principal en", f"{g:.2f}s")
    ok = not errs and not missing and not gaps
    print("VALIDACIÓN:", "OK" if ok else "CON PROBLEMAS")
    return ok

if __name__ == "__main__":
    P = project_from_argv()
    drafts = P.cfg.get("capcut_drafts_dir") or os.path.expandvars(r"%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft")
    sys.exit(0 if validate(os.path.join(drafts, P.cfg["name"], "draft_content.json")) else 1)
