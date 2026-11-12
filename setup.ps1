# Instalador del editor de video Claude -> CapCut (Windows).
# Uso (desde la carpeta del repo):  powershell -ExecutionPolicy Bypass -File setup.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
function Step($m) { Write-Host "`n==> $m" -ForegroundColor Cyan }
function Have($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }

Step "Python 3.10+"
$py = $null
foreach ($c in "py", "python") {
    if (Have $c) {
        $v = & $c -c "import sys;print('%d.%d' % sys.version_info[:2])" 2>$null
        if ($v -and [version]$v -ge [version]"3.10") { $py = $c; break }
    }
}
if (-not $py) {
    if (Have winget) {
        Write-Host "Instalando Python 3.12 con winget..."
        winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
        Write-Host "Cierra y vuelve a abrir la terminal, y ejecuta setup.ps1 de nuevo." -ForegroundColor Yellow; exit 1
    }
    throw "Instala Python 3.10+ desde https://www.python.org/downloads/ y vuelve a ejecutar."
}
Write-Host "OK: $py ($(& $py --version))"

Step "ffmpeg"
if (-not (Have ffmpeg)) {
    if (Have winget) {
        winget install -e --id Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
        Write-Host "ffmpeg instalado. Cierra y vuelve a abrir la terminal, y ejecuta setup.ps1 de nuevo." -ForegroundColor Yellow; exit 1
    }
    throw "Instala ffmpeg (https://www.gyan.dev/ffmpeg/builds/) y añádelo al PATH."
}
Write-Host "OK: $((Get-Command ffmpeg).Source)"

Step "Entorno Python (.venv) y dependencias"
if (-not (Test-Path ".venv")) { & $py -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) { throw "Falló pip install" }

Step "Modelo de transcripción (faster-whisper medium, ~1.5 GB, solo la primera vez)"
& .\.venv\Scripts\python.exe -c "from faster_whisper import WhisperModel; WhisperModel('medium', device='cpu', compute_type='int8'); print('OK modelo listo')"

Step "Comprobación final"
& .\.venv\Scripts\python.exe engine\run.py doctor
Write-Host "`nListo. Abre Claude Code en esta carpeta y pide: 'edita el video de <carpeta de brutos>'." -ForegroundColor Green
