"""Diferencias entre Windows y macOS en un solo sitio: carpeta de borradores de CapCut, fuentes por defecto,
Python del entorno y utilidades del sistema. El resto del motor no debe preguntar por el sistema operativo."""
import os, sys, shutil, glob

IS_WIN = os.name == "nt"
IS_MAC = sys.platform == "darwin"
OS_NAME = "windows" if IS_WIN else "mac" if IS_MAC else "linux"

def venv_python(repo):
    return os.path.join(repo, ".venv", "Scripts", "python.exe") if IS_WIN else os.path.join(repo, ".venv", "bin", "python")

def capcut_drafts_dir():
    """Carpeta de borradores de CapCut Desktop. Se puede forzar con la variable CAPCUT_DRAFTS_DIR
    o con "capcut_drafts_dir" en project.json (si en CapCut cambiaste Ajustes > Borrador > Guardar en)."""
    env = os.environ.get("CAPCUT_DRAFTS_DIR")
    if env: return env.replace("\\", "/")
    if IS_WIN:
        return os.path.expandvars(r"%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft").replace("\\", "/")
    home = os.path.expanduser("~")
    cands = [f"{home}/Movies/CapCut/User Data/Projects/com.lveditor.draft",
             f"{home}/Library/Containers/com.lemon.lvoverseas/Data/Movies/CapCut/User Data/Projects/com.lveditor.draft"]
    for c in cands:
        if os.path.isdir(c): return c
    return cands[0]

def native_path(p):
    """Ruta con el separador del sistema (CapCut guarda así algunas rutas en su lista de proyectos)."""
    return p.replace("/", "\\") if IS_WIN else p.replace("\\", "/")

# ---------- fuentes por defecto (las de la marca, si existen, tienen prioridad) ----------
_WIN_FONTS = {"black": "C:/Windows/Fonts/seguibl.ttf", "bold": "C:/Windows/Fonts/segoeuib.ttf",
              "semi": "C:/Windows/Fonts/seguisb.ttf", "reg": "C:/Windows/Fonts/segoeui.ttf",
              "emoji": "C:/Windows/Fonts/seguiemj.ttf", "sym": "C:/Windows/Fonts/seguisym.ttf"}
_MAC_DIRS = ["/System/Library/Fonts/Supplemental", "/Library/Fonts", "/System/Library/Fonts", os.path.expanduser("~/Library/Fonts")]
_MAC_WANT = {"black": ["Arial Black.ttf", "Arial Bold.ttf"], "bold": ["Arial Bold.ttf"], "semi": ["Arial Bold.ttf"],
             "reg": ["Arial.ttf"], "emoji": ["Arial Unicode.ttf", "Arial.ttf"], "sym": ["Arial Unicode.ttf", "Arial.ttf"]}

def _find_mac(names):
    for n in names:
        for d in _MAC_DIRS:
            p = os.path.join(d, n)
            if os.path.exists(p): return p
    return None

def default_fonts():
    if IS_WIN: return dict(_WIN_FONTS)
    out = {}
    for k, names in _MAC_WANT.items():
        p = _find_mac(names) if IS_MAC else None
        if not p:  # Linux u otro: DejaVu si está
            p = next(iter(glob.glob("/usr/share/fonts/**/DejaVuSans-Bold.ttf", recursive=True)), None)
        out[k] = p
    return out

DEFAULT_FONT_LABEL = "Segoe UI" if IS_WIN else "Arial"

def browser():
    """Chrome o Edge para convertir SVG si PyMuPDF no puede (opcional)."""
    cands = ([r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe"] if IS_WIN else
             ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
              "/Applications/Chromium.app/Contents/MacOS/Chromium"])
    for c in cands:
        if os.path.exists(c): return c
    for n in ("msedge", "google-chrome", "chromium", "chrome"):
        if shutil.which(n): return shutil.which(n)
    return None
