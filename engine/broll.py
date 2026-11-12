"""Paso 6 · Tomas de apoyo animadas (motion graphics a pantalla completa) del proyecto.
Las escenas viven en projects/<video>/broll_scenes.py (ver engine/scenes_api.py y el ejemplo).

  python engine/run.py broll-preview projects/x [escena ...]   -> broll/_prev_<escena>.jpg (4 fotogramas)
  python engine/run.py broll-render  projects/x [escena ...]   -> broll/<escena>.mp4 + broll/broll.json
"""
import importlib.util, json, os, sys
from common import Project
import mg, scenes_api
from timeline import Timeline

def main(mode, proj_dir, names):
    P = Project(proj_dir)
    mg.setup(P)
    scenes_api.TL = Timeline(P)
    path = P.p("broll_scenes.py")
    if not os.path.exists(path):
        print("Este proyecto no tiene broll_scenes.py: sin tomas de apoyo."); return
    spec = importlib.util.spec_from_file_location("broll_scenes", path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    out = P.p("broll"); meta_path = os.path.join(out, "broll.json")
    meta = json.load(open(meta_path, encoding="utf-8")) if os.path.exists(meta_path) else {}
    for name in names or list(scenes_api.SCENES):
        sc = scenes_api.SCENES[name]
        dur = round((sc["end"] - sc["start"]) * mg.FPS) / mg.FPS
        f = sc["fn"]()
        if mode == "preview":
            mg.render(os.path.join(out, f"_prev_{name}.jpg"), dur, f, preview_at=[dur * k for k in (0.08, 0.3, 0.55, 0.92)])
        else:
            mg.render(os.path.join(out, f"{name}.mp4"), dur, f)
            meta[name] = {"start": sc["start"], "end": sc["start"] + dur, "dur": dur, "outro": sc["outro"]}
        print(f"{name}: {sc['start']:.2f}-{sc['start'] + dur:.2f} ({dur:.2f}s){' [cierre]' if sc['outro'] else ''}", flush=True)
    if mode == "render":
        json.dump(meta, open(meta_path, "w", encoding="utf-8"), indent=1)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
