#!/usr/bin/env bash
# Instalador del editor de video Claude -> CapCut (macOS).
# Lo normal es no ejecutarlo a mano: abre Claude Code en esta carpeta y escribe INSTALAR.
# A mano (desde la carpeta del repo):  bash setup.sh
# Es idempotente: si algo ya está instalado, lo salta.
set -u
cd "$(dirname "$0")"
step() { printf '\n==> %s\n' "$1"; }
fail() { printf '\n%s\n' "$1"; exit 1; }

if [ "$(uname)" != "Darwin" ]; then fail "INSTALAR_FALLO sistema: este instalador es para Mac. En Windows usa setup.ps1."; fi

# Homebrew (si existe) en el PATH de esta sesión: Apple Silicon e Intel
for b in /opt/homebrew/bin/brew /usr/local/bin/brew; do
  if [ -x "$b" ]; then eval "$("$b" shellenv)"; break; fi
done
have() { command -v "$1" >/dev/null 2>&1; }

find_python() {
  for c in python3.13 python3.12 python3.11 python3.10 python3; do
    if have "$c" && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
      command -v "$c"; return 0
    fi
  done
  return 1
}

step "Python 3.10+"
PY="$(find_python || true)"
if [ -z "$PY" ]; then
  if have brew; then
    echo "Instalando Python con Homebrew..."
    brew install python@3.12 || true
    PY="$(find_python || true)"
  fi
  [ -n "$PY" ] || fail "INSTALAR_FALLO homebrew: falta Python 3.10+ y no hay Homebrew. Instala Homebrew (https://brew.sh, pide la contraseña del Mac) y vuelve a ejecutar."
fi
echo "OK: $PY ($("$PY" --version))"

step "ffmpeg"
if ! have ffmpeg || ! have ffprobe; then
  if have brew; then
    echo "Instalando ffmpeg con Homebrew (puede tardar unos minutos)..."
    brew install ffmpeg || true
  fi
  { have ffmpeg && have ffprobe; } || fail "INSTALAR_FALLO homebrew: falta ffmpeg y no hay Homebrew. Instala Homebrew (https://brew.sh) y vuelve a ejecutar."
fi
echo "OK: $(command -v ffmpeg)"

step "Entorno Python (.venv) y dependencias"
[ -x .venv/bin/python ] || "$PY" -m venv .venv || fail "INSTALAR_FALLO venv: no se pudo crear el entorno .venv"
.venv/bin/python -m pip install --upgrade pip --quiet
.venv/bin/python -m pip install -r requirements.txt --quiet || fail "INSTALAR_FALLO pip: falló pip install -r requirements.txt"
echo "OK: dependencias instaladas"

step "Modelo de transcripción (faster-whisper medium, ~1.5 GB, solo la primera vez)"
.venv/bin/python -c "from faster_whisper import WhisperModel; WhisperModel('medium', device='cpu', compute_type='int8'); print('OK modelo listo')" \
  || fail "INSTALAR_FALLO modelo: no se pudo descargar el modelo (revisa la conexión y el espacio libre)."

step "Comprobación final"
if .venv/bin/python engine/run.py doctor; then
  printf '\nINSTALAR_OK. Pide en Claude Code: "edita el video de <carpeta de brutos>".\n'
else
  printf '\nINSTALAR_INCOMPLETO: revisa las líneas que no dicen OK.\n'; exit 2
fi
