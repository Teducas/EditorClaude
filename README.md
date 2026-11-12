# Editor de video Claude → CapCut

Le das a Claude Code la carpeta con los brutos de alguien hablando a cámara y te devuelve un **proyecto editable de CapCut Desktop** con:

- **Cortes limpios:** sin muletillas, silencios ni repeticiones, eligiendo la mejor toma y ordenando el discurso.
- **Reencuadres alternos** (plano abierto, medio y cerrado) en cada corte, aprovechando el 4K para disimular los saltos.
- **Tomas de apoyo animadas** (motion graphics) con tu marca, sincronizadas con lo que se dice.
- **Tarjetas laterales** cuyos puntos aparecen al decirlos, más rótulo de nombre, título y logo.
- **Subtítulos dinámicos** como texto editable de CapCut, con palabras clave resaltadas.
- **Voz limpia y nivelada**, con música y efectos originales sin derechos.

Todo queda en pistas separadas de CapCut para que lo retoques y exportes desde ahí.

## Requisitos

- Windows 10/11 con **CapCut Desktop** instalado (probado con CapCut 9.7).
- **Claude Code**, ya sea la app de escritorio o la CLI.
- Unos 3 GB libres: el modelo de transcripción, más los medios de cada proyecto.
- Python 3.10+ y ffmpeg no hace falta instalarlos: el instalador los pone con `winget` si faltan.

## Instalación (una vez)

1. Clona el repositorio:

   ```bash
   git clone https://github.com/juanmarin-ctrl/claude-capcut-editor.git
   ```

2. Abre Claude Code en la carpeta `claude-capcut-editor`.
3. Escribe:

   > **INSTALAR**

Claude hace el resto. Revisa el sistema y ejecuta `setup.ps1`, que:
- Instala Python y ffmpeg si faltan.
- Crea el entorno `.venv` e instala las dependencias.
- Descarga el modelo de transcripción, de 1,5 GB. Solo pasa la primera vez.

Al final, el diagnóstico `doctor` dice si todo está listo. Claude también te ofrece crear tu marca. Si algo falla, te dice qué hacer. Volver a escribir INSTALAR sigue donde se quedó.

<details><summary>Instalar a mano, sin Claude</summary>

```bash
cd claude-capcut-editor
```

```bash
powershell -ExecutionPolicy Bypass -File setup.ps1
```

</details>

## Uso

1. Abre Claude Code **en la carpeta del repo**: así carga la skill `editar-video-capcut` y el `CLAUDE.md`.
2. Pídele, por ejemplo:

   > Edita el video de `D:\Brutos\Clase 3`: quita muletillas y silencios, agrega tomas de apoyo y motion graphics, y déjalo listo en CapCut. Usa mi marca `mi-marca`.

3. Claude sigue el flujo de la skill y te va mostrando hojas de control: transcripción, revisión del corte, animaciones y tarjetas.
4. Cuando te lo pida, **cierra CapCut**.
5. Al terminar, abre CapCut: el proyecto aparece en tu lista con el nombre elegido.

### Tu marca

Copia `brands/demo` a `brands/mi-marca` y cambia:
- `brand.json`: colores por rol (`primary`, `deep`, `accent`, `accent2`, `light`, `muted`, `panel`) y fuentes.
- `logo_light.png`: logo en blanco o claro, con fondo transparente.

Las carpetas de marca, salvo `demo`, no se suben a git.

## Cómo funciona

```
brutos ─► transcribe ─► (Claude decide el montaje en project.json) ─► cuts ─► check
       ─► media ─► broll (escenas que escribe Claude) ─► overlays ─► audio ─► build ─► CapCut
```

| Carpeta | Contenido |
|---|---|
| `engine/` | Motor: transcripción (faster-whisper), cortes por energía y palabras, motor de animación (PIL → ffmpeg), tarjetas, audio, constructor del borrador de CapCut, validador |
| `template/capcut_template.json` | Plantilla anónima extraída de un borrador real de CapCut 9.7. CapCut no documenta su formato, así que se clonan objetos de un borrador que él mismo guardó |
| `.claude/skills/editar-video-capcut/` | El flujo de trabajo y las reglas editoriales para Claude |
| `examples/ramon-video1/` | Un montaje real completo (`project.json` y `broll_scenes.py`) como referencia |
| `brands/` | Identidades visuales |
| `projects/` | Tus videos, uno por carpeta (ignorado por git) |

### Comandos (por si quieres ejecutarlos a mano)

```bash
.venv\Scripts\python engine\run.py help
```

## Si CapCut no abre el proyecto

Las versiones de CapCut cambian su formato interno. Haz esto:
1. En tu CapCut, crea un proyecto con un video, una imagen, un texto, un audio y un fotograma clave.
2. Ciérralo y ejecuta:

```bash
.venv\Scripts\python engine\make_template.py "%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\<nombre de ese proyecto>"
```

3. Vuelve a ejecutar `build`. La plantilla nueva sale de tu propia versión de CapCut y se anonimiza automáticamente.

## Limitaciones

- Pensado para tomas a cámara fija de una persona. El reencuadre asume la cara en una posición parecida en todas las tomas (`framing` en `project.json`).
- Solo Windows: las rutas de CapCut y las fuentes Segoe UI son de Windows.
- La música y los efectos son sintetizados: discretos, no de biblioteca. Puedes cambiarlos por pistas de CapCut Pro.
