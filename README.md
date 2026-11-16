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

- **Windows 10/11 o Mac**, con **CapCut Desktop** instalado (probado con CapCut 9.7 en Windows).
- **Claude Code**, ya sea la app de escritorio o la CLI.
- Unos 3 GB libres: el modelo de transcripción, más los medios de cada proyecto.
- Python 3.10+ y ffmpeg no hace falta instalarlos: el instalador los pone si faltan. En Windows usa `winget`; en Mac, Homebrew. Si el Mac no tiene Homebrew, Claude te pide pegar una línea en Terminal: Homebrew pide la contraseña del Mac.

## Instalación (una vez)

1. **Descarga el editor:** en esta página, pulsa el botón verde **Code** y luego **Download ZIP**. No necesitas cuenta de GitHub.
2. **Descomprímelo:**
   - **Windows:** en Descargas, haz clic derecho en el ZIP y elige **Extraer todo**.
   - **Mac:** haz doble clic en el ZIP; el Mac lo descomprime solo.

   Después mueve la carpeta donde quieras (por ejemplo, a Documentos).
3. **Abre Claude Code en esa carpeta:** la que tiene dentro el archivo `README.md` y la carpeta `engine`. Si al extraer ves una carpeta dentro de otra con el mismo nombre, entra en la de dentro.
4. Escribe:

   > **INSTALAR**

Claude hace el resto. Revisa el sistema y ejecuta el instalador (`setup.ps1` en Windows, `setup.sh` en Mac), que:
- Instala Python y ffmpeg si faltan.
- Crea el entorno `.venv` e instala las dependencias.
- Descarga el modelo de transcripción, de 1,5 GB. Solo pasa la primera vez.

Al final, el diagnóstico `doctor` dice si todo está listo. Si algo falla, te dice qué hacer. Volver a escribir INSTALAR sigue donde se quedó.

<details><summary>Si sabes usar git, o quieres instalar a mano sin Claude</summary>

```bash
git clone https://github.com/juanmarin-ctrl/claude-capcut-editor.git
```

```bash
cd claude-capcut-editor
```

En Windows:

```bash
powershell -ExecutionPolicy Bypass -File setup.ps1
```

En Mac:

```bash
bash setup.sh
```

</details>

## Uso

1. Abre Claude Code **en la carpeta del repo**: así carga la skill `editar-video-capcut` y el `CLAUDE.md`.
2. Pídele, por ejemplo:

   > Edita el video de `D:\Brutos\Clase 3` con la marca de Café Andino.

   En Mac, arrastra la carpeta de brutos a la ventana de Claude Code para pegar su ruta.

3. Claude sigue el flujo de la skill y te va mostrando hojas de control: transcripción, revisión del corte, animaciones y tarjetas.
4. Cuando te lo pida, **cierra CapCut**.
5. Al terminar, abre CapCut: el proyecto aparece en tu lista con el nombre elegido.

### La marca del cliente

**Copia el branding del cliente en la carpeta `marcas`, en una subcarpeta con su nombre, sin importar el formato:** manual en PDF, logos en AI, SVG, PNG o JPG, presentaciones, un ZIP o fuentes.
No hace falta convertir, renombrar ni ordenar nada.

Después dile a Claude *«Ya pegué el branding de Café Andino»*, o pídele directamente el video con esa marca. Claude:
- saca los colores, el logo en blanco (le quita el fondo) y las tipografías;
- te enseña una muestra de cómo se verán las tarjetas, los rótulos y los subtítulos;
- lo cambia si le pides algo como «el naranja más oscuro» o «usa el otro logo».

Las marcas de tus clientes se quedan en tu equipo: no se suben a git.

## Cómo funciona

```
brutos ─► transcribe ─► (Claude decide el montaje en project.json) ─► cuts ─► check
       ─► media ─► broll (escenas que escribe Claude) ─► overlays ─► audio ─► build ─► CapCut
```

| Carpeta | Contenido |
|---|---|
| `engine/` | Motor: transcripción (faster-whisper), cortes por energía y palabras, motor de animación (PIL → ffmpeg), tarjetas, audio, constructor del borrador de CapCut, validador |
| `template/capcut_template.json` | Plantilla anónima extraída de un borrador real de CapCut 9.7. CapCut no documenta su formato, así que se clonan objetos de un borrador que él mismo guardó |
| `.claude/skills/` | Las instrucciones para Claude: `instalar`, `marca` (branding en cualquier formato) y `editar-video-capcut` (flujo y reglas editoriales) |
| `examples/ramon-video1/` | Un montaje real completo (`project.json` y `broll_scenes.py`) como referencia |
| `marcas/` | El branding de cada cliente, tal como llegó; Claude genera aquí `brand.json` y el logo en blanco |
| `projects/` | Tus videos, uno por carpeta (ignorado por git) |

### Comandos (por si quieres ejecutarlos a mano)

En Windows:

```bash
.venv\Scripts\python engine\run.py help
```

En Mac:

```bash
.venv/bin/python engine/run.py help
```

## Si CapCut no abre el proyecto

Las versiones de CapCut cambian su formato interno. Haz esto:
1. En tu CapCut, crea un proyecto con un video, una imagen, un texto, un audio y un fotograma clave.
2. Ciérralo y ejecuta:

En Windows:

```bash
.venv\Scripts\python engine\make_template.py "%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\<nombre de ese proyecto>"
```

En Mac:

```bash
.venv/bin/python engine/make_template.py ~/Movies/CapCut/"User Data"/Projects/com.lveditor.draft/"<nombre de ese proyecto>"
```

O, más fácil: pídele a Claude *«CapCut no abre el proyecto, regenera la plantilla con mi proyecto de prueba»*.

3. Vuelve a ejecutar `build`. La plantilla nueva sale de tu propia versión de CapCut y se anonimiza automáticamente.

## Limitaciones

- Pensado para tomas a cámara fija de una persona. El reencuadre asume la cara en una posición parecida en todas las tomas (`framing` en `project.json`).
- **Mac: compatible, pero aún sin comprobar en un Mac real.**
  - La plantilla incluida sale de CapCut 9.7 en Windows.
  - En Mac el editor escribe también los archivos que usa CapCut para Mac (`draft_info.json`).
  - Si tu CapCut para Mac no abre el primer proyecto, regenera la plantilla con un proyecto de prueba, como se explica arriba. A partir de ahí queda hecha con tu propio CapCut.
  - Si tu versión de CapCut guarda los borradores cifrados, el editor no puede leer ese proyecto de prueba: te lo dirá.
- **Fuentes por defecto:** Segoe UI en Windows y Arial en Mac. Con las fuentes de la marca se ve igual en los dos.
- **Carpeta de CapCut:** si la cambiaste en Ajustes › Borrador, indica la nueva con `"capcut_drafts_dir"` en el `project.json` o con la variable `CAPCUT_DRAFTS_DIR`.
- La música y los efectos son sintetizados: discretos, no de biblioteca. Puedes cambiarlos por pistas de CapCut Pro.
