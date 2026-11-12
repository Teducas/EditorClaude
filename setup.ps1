# Instalador del editor de video Claude -> CapCut (Windows).
# Lo normal es no ejecutarlo a mano: abre Claude Code en esta carpeta y escribe INSTALAR.
# A mano (desde la carpeta del repo):  powershell -ExecutionPolicy Bypass -File setup.ps1
# Es idempotente: si algo ya está instalado, lo salta. Si winget instala Python o ffmpeg,
# recarga el PATH y sigue en la misma ejecución (no hace falta reabrir la terminal).
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
function Step($m) { Write-Host "`n==> $m" -ForegroundColor Cyan }
function Have($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }
function Reload-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
}
function Find-Python {
    foreach ($c in "py", "python") {
        if (Have $c) {
            $v = & $c -c "import sys;print('%d.%d' % sys.version_info[:2])" 2>$null
            if ($v -and [version]$v -ge [version]"3.10") { return $c }
        }
    }
    return $null
}
function Winget-Install($id) {
    if (-not (Have winget)) { return $false }
    Write-Host "Instalando $id con winget..."
    winget install -e --id $id --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
    Reload-Path
    return $true
}

Step "Python 3.10+"
$py = Find-Python
if (-not $py) {
    if (Winget-Install "Python.Python.3.12") { $py = Find-Python }
    if (-not $py) {
        # winget a veces deja Python en la carpeta del usuario sin tocar el PATH de esta sesión
        $cand = Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe" -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1
        if ($cand) { $py = $cand.FullName }
    }
    if (-not $py) { throw "INSTALAR_FALLO python: instala Python 3.10+ desde https://www.python.org/downloads/ y vuelve a ejecutar." }
}
Write-Host "OK: $py ($(& $py --version))"

Step "ffmpeg"
if (-not (Have ffmpeg)) {
    Winget-Install "Gyan.FFmpeg" | Out-Null
    if (-not (Have ffmpeg)) {
        $ff = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Gyan.FFmpeg*\*\bin\ffmpeg.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($ff) { $env:Path = $ff.DirectoryName + ";" + $env:Path }
    }
    if (-not (Have ffmpeg)) { throw "INSTALAR_FALLO ffmpeg: instala ffmpeg (https://www.gyan.dev/ffmpeg/builds/) y añádelo al PATH." }
}
Write-Host "OK: $((Get-Command ffmpeg).Source)"

Step "Entorno Python (.venv) y dependencias"
if (-not (Test-Path ".venv\Scripts\python.exe")) { & $py -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) { throw "INSTALAR_FALLO pip: falló pip install -r requirements.txt" }
Write-Host "OK: dependencias instaladas"

Step "Modelo de transcripción (faster-whisper medium, ~1.5 GB, solo la primera vez)"
& .\.venv\Scripts\python.exe -c "from faster_whisper import WhisperModel; WhisperModel('medium', device='cpu', compute_type='int8'); print('OK modelo listo')"
if ($LASTEXITCODE -ne 0) { throw "INSTALAR_FALLO modelo: no se pudo descargar el modelo (revisa la conexión y el espacio libre)." }

Step "Comprobación final"
& .\.venv\Scripts\python.exe engine\run.py doctor
if ($LASTEXITCODE -ne 0) { Write-Host "`nINSTALAR_INCOMPLETO: revisa las líneas que no dicen OK." -ForegroundColor Yellow; exit 2 }
Write-Host "`nINSTALAR_OK. Pide en Claude Code: 'edita el video de <carpeta de brutos>'." -ForegroundColor Green
