"""Rutas y configuración compartidas. Cada video es una carpeta de proyecto con project.json."""
import json, os, re, sys, subprocess, shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV_PY = os.path.join(REPO, ".venv", "Scripts" if os.name == "nt" else "bin", "python.exe" if os.name == "nt" else "python")

class Project:
    def __init__(self, path):
        self.dir = os.path.abspath(path)
        self.cfg_path = os.path.join(self.dir, "project.json")
        self.cfg = json.load(open(self.cfg_path, encoding="utf-8-sig"))  # tolera BOM (Bloc de notas)
        for d in ("work", "media", "broll", "overlays", "audio"):
            os.makedirs(self.p(d), exist_ok=True)
        b = self.cfg.get("brand", "demo")
        self.brand_dir = b if os.path.isabs(b) else os.path.join(REPO, "brands", b)
        self.brand = json.load(open(os.path.join(self.brand_dir, "brand.json"), encoding="utf-8-sig"))

    def p(self, *parts): return os.path.join(self.dir, *parts)
    @property
    def source_dir(self):
        s = self.cfg["source_dir"]
        return s if os.path.isabs(s) else os.path.normpath(os.path.join(self.dir, s))
    def save(self):
        json.dump(self.cfg, open(self.cfg_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    def clips(self):
        exts = (".mov", ".mp4", ".m4v", ".mkv")
        return sorted(os.path.splitext(f)[0] for f in os.listdir(self.source_dir) if f.lower().endswith(exts))
    def source_file(self, clip):
        for f in os.listdir(self.source_dir):
            if os.path.splitext(f)[0] == clip: return os.path.join(self.source_dir, f)
        raise FileNotFoundError(clip)

def project_from_argv():
    if len(sys.argv) < 2:
        sys.exit("Falta la carpeta del proyecto. Ej: python engine/run.py <paso> projects/mi-video")
    return Project(sys.argv[1])

def ffmpeg_ok():
    return shutil.which("ffmpeg") and shutil.which("ffprobe")

def read_audio(path, sr=16000):
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()

def parse_anchor(a):
    """'IMG_0136:4' | 'IMG_0136:9:e' | 'IMG_0136:9:e+0.3' -> (clip, idx, edge, offset)"""
    m = re.match(r"^(.+?):(\d+)(?::([se]))?([+-][\d.]+)?$", str(a))
    if not m: raise ValueError(f"Ancla inválida: {a!r} (usa CLIP:indice[:e][+seg])")
    return m.group(1), int(m.group(2)), m.group(3) or "s", float(m.group(4) or 0)
