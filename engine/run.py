"""Punto de entrada único del flujo. Ejecutar SIEMPRE con el Python del entorno (.venv):

  python engine/run.py doctor
  python engine/run.py marca         marcas/cliente      (analiza el branding en cualquier formato)
  python engine/run.py marca-aplicar marcas/cliente --logo <archivo> --colores primary=#hex,accent=#hex
  python engine/run.py init       projects/mi-video --source "D:/Brutos/Mi video" --brand demo --name "Mi video"
  python engine/run.py transcribe projects/mi-video
  (editar projects/mi-video/project.json -> "order", "fix", "keywords")
  python engine/run.py cuts       projects/mi-video
  python engine/run.py check      projects/mi-video
  python engine/run.py media      projects/mi-video
  python engine/run.py broll-preview / broll-render projects/mi-video [escena ...]
  python engine/run.py overlays   projects/mi-video
  python engine/run.py audio      projects/mi-video
  python engine/run.py build      projects/mi-video   (cierra CapCut antes)
  python engine/run.py validate   projects/mi-video
  python engine/run.py where      projects/mi-video IMG_0137:6   (segundo del montaje de una palabra)
"""
import json, os, sys, runpy, shutil, subprocess

ENGINE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ENGINE)
from common import REPO

STEPS = {"transcribe": "transcribe.py", "cuts": "cuts.py", "check": "check.py", "media": "prepare_media.py",
         "overlays": "overlays.py", "audio": "audio.py", "build": "build_draft.py", "validate": "validate_draft.py"}

def doctor():
    ok = True
    def line(good, msg):
        nonlocal ok; ok &= bool(good); print(("OK   " if good else "FALTA"), msg)
    line(sys.version_info >= (3, 10), f"Python {sys.version.split()[0]} (>= 3.10)")
    line(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg y ffprobe en el PATH")
    for mod in ("numpy", "scipy", "PIL", "faster_whisper", "fitz"):
        try: __import__(mod); line(True, f"módulo {mod}")
        except ImportError: line(False, f"módulo {mod} (ejecuta setup.ps1)")
    from platforms import capcut_drafts_dir, OS_NAME, default_fonts
    print(f"OK    sistema: {OS_NAME}")
    drafts = capcut_drafts_dir()
    line(os.path.isdir(drafts), f"CapCut Desktop (carpeta de borradores: {drafts})")
    fonts = default_fonts()
    line(all(fonts.get(k) and os.path.exists(fonts[k]) for k in ("black", "bold", "semi", "reg")), "fuentes del sistema para textos y animaciones")
    tpl = os.path.join(REPO, "template", "capcut_template.json")
    if os.path.exists(tpl):
        t = json.load(open(tpl, encoding="utf-8"))
        v, tos = t.get("capcut_version"), (t.get("skeleton", {}).get("platform") or {}).get("os", "?")
        print(f"OK    plantilla de CapCut (extraída de CapCut {v} en {tos}; si tu CapCut no abre los proyectos, regenera con engine/make_template.py)")
    else: line(False, "template/capcut_template.json")
    if shutil.which("ffmpeg"):
        from prepare_media import pick_encoder
        print("OK    codificador de video:", pick_encoder()[0])
    print("\nTodo listo." if ok else "\nFaltan piezas: ejecuta  powershell -ExecutionPolicy Bypass -File setup.ps1")
    return ok

def init(args):
    import argparse
    ap = argparse.ArgumentParser(prog="run.py init")
    ap.add_argument("project"); ap.add_argument("--source", required=True); ap.add_argument("--brand", default="demo")
    ap.add_argument("--name"); ap.add_argument("--language", default="es")
    a = ap.parse_args(args)
    os.makedirs(a.project, exist_ok=True)
    cfg_path = os.path.join(a.project, "project.json")
    if os.path.exists(cfg_path): sys.exit(f"Ya existe {cfg_path}")
    cfg = {"name": a.name or os.path.basename(os.path.abspath(a.project)), "source_dir": os.path.abspath(a.source).replace("\\", "/"),
           "brand": a.brand, "language": a.language, "whisper_model": "medium",
           "order": [], "fix": {}, "keywords": [], "cards": [], "lower_third": None, "title_pill": None, "logo_bug": True,
           "captions": {"enabled": True, "size": 7.5, "y": -0.80, "max_words": 4, "max_chars": 22},
           "framing": {"eyes_y": 0.36, "face_x": -0.08, "target_y": 0.33, "cycle": [1.0, 1.32, 1.0, 1.55]},
           "mix": {"music_db": -21, "outro_db": -8, "whoosh_db": -12, "pop_db": -17, "ding_db": -12}, "voice_lufs": -17.5}
    json.dump(cfg, open(cfg_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for d in ("work", "media", "broll", "overlays", "audio"):
        os.makedirs(os.path.join(a.project, d), exist_ok=True)
    from common import brand_dir
    if not os.path.exists(os.path.join(brand_dir(a.brand), "brand.json")):
        print(f"Aviso: la marca {a.brand} no está lista. Pega el branding en marcas/{a.brand}/ y ejecuta run.py marca marcas/{a.brand}.")
    print("Proyecto creado:", cfg_path)

def where(args):
    from common import Project
    from timeline import Timeline
    TL = Timeline(Project(args[0]))
    for a in args[1:]: print(a, "->", f"{TL.at(a):.2f}s")
    print(f"duración del montaje: {TL.total:.2f}s")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(__doc__); return
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "doctor": sys.exit(0 if doctor() else 1)
    if cmd == "init": return init(args)
    if cmd == "where": return where(args)
    if cmd in ("marca", "marca-aplicar"):
        import brand_kit
        if not args: sys.exit("Falta la carpeta de la marca. Ej: run.py marca marcas/cliente")
        return brand_kit.analizar(args[0]) if cmd == "marca" else brand_kit.aplicar(args[0], args[1:])
    if cmd in ("broll-preview", "broll-render"):
        import broll
        return broll.main(cmd.split("-")[1], args[0], args[1:])
    if cmd not in STEPS: sys.exit(f"Paso desconocido: {cmd}\n{__doc__}")
    sys.argv = [os.path.join(ENGINE, STEPS[cmd])] + args
    runpy.run_path(sys.argv[0], run_name="__main__")

if __name__ == "__main__":
    main()
