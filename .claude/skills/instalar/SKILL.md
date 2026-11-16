---
name: instalar
description: Instala el editor Claude → CapCut en este equipo (Windows o Mac) de principio a fin: Python, ffmpeg, entorno .venv, dependencias, modelo de transcripción y comprobación. Usar cuando el usuario escriba "INSTALAR", "instálalo", "instala todo", "configura el editor" o cuando `.venv` no exista o `run.py doctor` falle.
---

# INSTALAR: dejar el editor listo en este equipo

El usuario solo ha escrito «INSTALAR». Hazlo todo tú, sin pedirle que ejecute comandos, y háblale en español y sin tecnicismos: es diseñador, no programador.

## 0. ¿Windows o Mac?
Mira la plataforma del entorno (win32 o darwin), o ejecuta `uname` si dudas. Sigue solo la columna de su sistema.

| | Windows | Mac |
|---|---|---|
| Python del entorno | `.venv\Scripts\python` | `.venv/bin/python` |
| Instalador | `powershell -ExecutionPolicy Bypass -File setup.ps1` | `bash setup.sh` |
| Carpeta de CapCut | `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft` | `~/Movies/CapCut/User Data/Projects/com.lveditor.draft` |
| Python y ffmpeg | con winget, automático | con Homebrew |

## 1. Comprobaciones previas (rápidas, sin instalar nada)
- **Windows:**
  ```powershell
  (Get-PSDrive C).Free/1GB; Test-Path "$env:LOCALAPPDATA\CapCut\User Data\Projects\com.lveditor.draft"; Test-Path .venv\Scripts\python.exe
  ```
- **Mac:**
  ```bash
  sw_vers -productVersion; df -g ~ | tail -1; ls -d ~/Movies/CapCut/"User Data"/Projects/com.lveditor.draft; ls .venv/bin/python; command -v brew || ls /opt/homebrew/bin/brew /usr/local/bin/brew
  ```

Qué hacer con el resultado:
- **Menos de 3 GB libres:** avisa y pregunta si sigue igualmente.
- **No existe la carpeta de CapCut:** CapCut Desktop no está instalado o no se ha abierto nunca. Pídele que lo instale desde capcut.com, que lo abra una vez y que cree un proyecto vacío. Mientras tanto, sigue con el resto.
- **Mac sin Homebrew y sin Python 3.10+ o sin ffmpeg:** Homebrew pide la contraseña del Mac, así que tiene que instalarlo él.
  1. Explícale en una frase que hace falta un instalador de herramientas llamado Homebrew.
  2. Pídele que abra la app **Terminal**, pegue esta línea, pulse Enter y escriba su contraseña cuando la pida (no se ve al escribirla):
     ```
     /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
     ```
  3. Cuando diga que terminó, sigue con el paso 2.

## 2. Instalación
Dile en una línea que empieza y que la primera vez tarda unos minutos, porque descarga un modelo de 1,5 GB. Luego ejecuta el instalador de su sistema.
- Puede tardar más de 10 minutos, por el modelo y, en Mac, por ffmpeg. Ejecútalo en segundo plano (o con el tiempo de espera máximo) y espera a que termine. No lo lances dos veces.
- Es idempotente. Si se corta, volver a ejecutarlo continúa donde se quedó.

## 3. Lee el resultado
- **`INSTALAR_OK`:** todo bien.
- **`INSTALAR_FALLO <qué>`:** explica qué falta con la solución que da el mensaje. En Mac, `homebrew` significa que falta Homebrew (ver el paso 1). Cuando confirme, vuelve a ejecutar el instalador.
- **`INSTALAR_INCOMPLETO`:** mira qué líneas del `doctor` no dicen OK.
  - **CapCut:** ver el paso 1.
  - **Plantilla de CapCut:** si CapCut no abre luego los proyectos, se regenera con `engine/make_template.py`. Ver «Si CapCut no abre el proyecto» en el README.
  - **Codificador de vídeo:** no es grave, se usa el de CPU.

## 4. Mac: aviso sobre CapCut
La plantilla incluida se extrajo de CapCut 9.7 en **Windows**. En Mac el editor genera también los archivos que usa CapCut para Mac, pero todavía no está comprobado en un Mac real. Díselo con naturalidad: si el primer proyecto no abre en CapCut, se arregla en dos minutos creando un proyecto de prueba en su CapCut (ver el README).

## 5. Marca (opcional, pregúntalo)
Dile: «Si quieres, copia el branding de tu cliente, tal como te llegó y en cualquier formato, en la carpeta `marcas`, dentro de una carpeta con su nombre. Avísame y lo preparo».
Cuando avise, sigue `.claude/skills/marca/SKILL.md`.

## 6. Cierre
Responde con un resumen corto:
- Qué quedó instalado, con las líneas OK del `doctor`.
- Qué falta, si falta algo.
- La frase para empezar: «Edita el video de `<carpeta de tus brutos>` con la marca de <cliente>». En Mac puede arrastrar la carpeta a la ventana de Claude Code para pegar su ruta.
