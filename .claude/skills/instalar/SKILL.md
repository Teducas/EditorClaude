---
name: instalar
description: Instala el editor Claude → CapCut en este equipo de principio a fin (Python, ffmpeg, entorno .venv, dependencias, modelo de transcripción y comprobación). Usar cuando el usuario escriba "INSTALAR", "instálalo", "instala todo", "configura el editor" o cuando `.venv` no exista o `run.py doctor` falle.
---

# INSTALAR: dejar el editor listo en este equipo

El usuario solo ha escrito «INSTALAR». Hazlo todo tú, sin pedirle que ejecute comandos, y háblale en español y sin tecnicismos: es diseñador, no programador.

## 1. Comprobaciones previas (rápidas, sin instalar nada)
Ejecuta en PowerShell desde la raíz del repo:

```powershell
[Environment]::OSVersion.Version; (Get-PSDrive C).Free/1GB; Test-Path "$env:LOCALAPPDATA\CapCut\User Data\Projects\com.lveditor.draft"; Test-Path .venv\Scripts\python.exe
```

- **No es Windows:** para y explica que el editor solo funciona en Windows 10/11.
- **Menos de 3 GB libres en C:** avisa y pregunta si sigue igualmente.
- **No existe la carpeta de borradores de CapCut:** CapCut Desktop no está instalado o no se ha abierto nunca. Pídele que lo instale desde capcut.com, que lo abra una vez y que cree un proyecto vacío. Mientras tanto, sigue con el resto: el resultado se valida al final con `doctor`.

## 2. Instalación
Dile en una línea que empieza y que la primera vez tarda unos minutos, porque descarga un modelo de 1,5 GB. Luego ejecuta:

```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
```

- Puede tardar más de 10 minutos por la descarga del modelo. Ejecútalo en segundo plano (o con el tiempo de espera máximo) y espera a que termine. No lo lances dos veces.
- Es idempotente. Si se corta, volver a ejecutarlo continúa donde se quedó.
- Si winget instala Python o ffmpeg, el propio script recarga el PATH y sigue. No hace falta reabrir la terminal.

## 3. Lee el resultado
- **`INSTALAR_OK`:** todo bien.
- **`INSTALAR_FALLO <qué>`:** explica qué falta con la solución que da el mensaje. Si es Python o ffmpeg sin winget, dale el enlace. Cuando confirme, vuelve a ejecutar `setup.ps1`.
- **`INSTALAR_INCOMPLETO`:** mira qué líneas del `doctor` no dicen OK.
  - **CapCut:** ver el paso 1.
  - **Plantilla de CapCut:** si CapCut no abre luego los proyectos, se regenera con `engine/make_template.py`. Ver la sección «Si CapCut no abre el proyecto» del README.
  - **Codificador de vídeo:** no es grave, se usa el de CPU.

## 4. Marca (opcional, pregúntalo)
Pregunta si quiere crear ya su marca. Si dice que sí:
1. Pídele el nombre, los colores (o el manual de marca) y el logo en blanco con fondo transparente.
2. Copia `brands/demo` a `brands/<nombre-en-minusculas-con-guiones>`.
3. Rellena `brand.json` con los colores por rol: `primary`, `deep`, `accent`, `accent2`, `light`, `muted` y `panel`.
4. Pon el logo como `logo_light.png`.

## 5. Cierre
Responde con un resumen corto:
- Qué quedó instalado, con las líneas OK del `doctor`.
- Qué falta, si falta algo.
- La frase para empezar: «Edita el video de `D:\ruta\a\tus\brutos` con mi marca `<marca>`».
