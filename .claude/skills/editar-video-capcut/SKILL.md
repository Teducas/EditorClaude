---
name: editar-video-capcut
description: Edita videos de una persona hablando a cámara (clases, cursos, talking heads) y entrega un proyecto EDITABLE de CapCut Desktop. Quita muletillas, silencios y repeticiones, reordena tomas, reencuadra, crea tomas de apoyo animadas (motion graphics), tarjetas sincronizadas con la voz, subtítulos dinámicos, música y efectos originales. Usar cuando pidan editar/montar/cortar un video, "quitar muletillas", "tomas de apoyo", "motion graphics" o "exportar a CapCut".
---

# Editar video → proyecto de CapCut

Todo se ejecuta desde la raíz del repo con el Python del entorno:

```
.venv\Scripts\python engine\run.py <paso> projects/<video> [...]
```

Si `.venv` no existe o `run.py doctor` falla, ejecuta `powershell -ExecutionPolicy Bypass -File setup.ps1` primero.
El ejemplo completo y real está en `examples/ramon-video1/` (project.json + broll_scenes.py): léelo antes de empezar un video nuevo.

## Flujo

1. **Crear el proyecto**
   `run.py init projects/<video> --source "<carpeta de brutos>" --brand <marca> --name "<nombre en CapCut>"`
   Marca: carpeta en `brands/` con `brand.json` (colores, fuentes) y logo claro. Si el usuario no tiene, usa `demo` y ofrece crear la suya.
   Mira los brutos antes de decidir nada: `ffprobe` (duración, resolución, rotación) y una hoja de miniaturas con ffmpeg.

2. **Transcribir** — `run.py transcribe projects/<video>` → lee `work/transcript.txt`
   Formato: `índice:palabra@segundo`, `[0.54]` = pausa, `?` = palabra dudosa.

3. **Decidir el montaje** (esto es criterio editorial, hazlo tú) en `project.json`:
   - `order`: orden narrativo de tomas y rangos de palabras que se quedan `{"clip": "IMG_0159", "keep": [[0, 6], [8, 23]]}`.
     - Tomas repetidas: quédate con la más limpia y completa, descarta las demás.
     - Arranques en falso y repeticiones dentro de una toma ("te voy a pedir porque vamos…, te voy a pedir…"): sácalas partiendo el rango.
     - Reordena si mejora la narrativa (que cada bloque lleve al siguiente; cierre = despedida + próximo video).
   - `fix`: corrige palabras mal transcritas para los subtítulos (`"IMG_0132:9": "agente"`).
   - `keywords`: palabras que se resaltan en color en los subtítulos.
   Anota las decisiones en `_order_notas` y cuéntaselas al usuario.

4. **Cortar** — `run.py cuts` (silencios > 0.2 s, muletillas sostenidas, sin invadir palabras descartadas).

5. **Controlar el corte** — `run.py check` → lee `work/check.txt` ENTERO y busca:
   - palabras perdidas (texto que falta respecto a la transcripción): suele ser voz baja → baja `voice_threshold` (por defecto 0.20) o amplía el rango;
   - repeticiones que se colaron → ajusta los rangos de `order`;
   - `<<MULETILLA?` y `<<VACÍO` → revisa ese segmento.
   Repite 4–5 hasta que el texto se lea limpio.

6. **Preparar medios** — `run.py media` (hornea la rotación del iPhone, nivela y limpia la voz, conserva 4K para acercar sin perder nitidez).

7. **Tomas de apoyo** (motion graphics a pantalla completa) — escribe `projects/<video>/broll_scenes.py` (ver ejemplo y `engine/scenes_api.py`):
   - 5–8 escenas en los momentos que se explican mejor con una imagen (conceptos, listas, comparaciones, metáforas), de 3–11 s, sincronizadas con palabras (`at("IMG_0137:6")`).
   - Una escena `outro=True` como placa final.
   - Usa la identidad de la marca (`mg.ACCENT`, `mg.PRIMARY`, `logo()`), fondo `background()` + `drift()`.
   - Deja libres los 200 px inferiores (subtítulos) y no pongas texto en el borde.
   - `run.py broll-preview` → MIRA cada `broll/_prev_*.jpg` y corrige solapes, elementos fuera de cuadro, huecos vacíos al inicio. Solo entonces `run.py broll-render`.

8. **Tarjetas y rótulos** en `project.json` (`cards`, `lower_third`, `title_pill`, `logo_bug`) → `run.py overlays` → MIRA `work/overlays_sheet.jpg`.
   - Van sobre la pared vacía a la izquierda (`L`) o derecha (`R`) del orador; alterna lados.
   - Cada punto aparece cuando se dice su palabra ancla. `*texto*` = color de acento. Cabeceras cortas (≤ 18 caracteres).
   - Si el orador tiene otra posición en cuadro, ajusta `card_margin`/`card_top` y `framing`.

9. **Música y efectos** — `run.py audio` (originales, sin derechos).

10. **Construir el borrador** — pide al usuario que CIERRE CapCut, luego `run.py build` y `run.py validate`.
    El proyecto aparece en CapCut con el nombre de `name`. Si CapCut no lo abre, regenera la plantilla desde un
    borrador guardado por SU CapCut con `.venv\Scripts\python engine\make_template.py "<carpeta de un borrador>"`
    (un borrador con al menos un video, una imagen, un texto, un audio y un keyframe) y vuelve a construir.

## Reglas

- No inventes contenido: tarjetas y animaciones dicen lo que dice el orador.
- No renderices el video final: la entrega es el proyecto de CapCut (el usuario exporta desde CapCut).
- Antes de cada paso caro (transcribir, preparar medios, renderizar escenas) avisa de cuánto tarda; ejecútalo en segundo plano si pasa de 2 min.
- Mira siempre las imágenes de control antes de seguir; no asumas que salieron bien.
- Los brutos no se modifican nunca; todo se genera en la carpeta del proyecto.
- `build` reescribe la lista de proyectos de CapCut (deja copia `root_meta_info.json.bak_claude`): CapCut debe estar cerrado.

## Referencia rápida

| Ajuste (project.json) | Para qué |
|---|---|
| `voice_threshold` | sensibilidad del detector de voz (bajar si se pierden palabras dichas en voz baja) |
| `min_silence`, `pad_in`, `pad_out` | cuánto silencio se corta y cuánto aire se deja en cada corte |
| `framing.eyes_y`, `framing.face_x` | posición de ojos/cara del orador en unidades de medio lienzo (arriba = +1, derecha = +1) |
| `framing.cycle` | zooms que se alternan en cada corte (4K permite hasta ~1.6) |
| `captions.size`, `captions.y` | tamaño y altura de subtítulos en CapCut |
| `mix.*_db` | volumen de música y efectos respecto a la voz |
| `voice_lufs` | nivel de la voz al preparar medios |
