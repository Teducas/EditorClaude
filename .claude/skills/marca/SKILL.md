---
name: marca
description: Prepara la marca de un cliente a partir de lo que el diseñador haya pegado en marcas/<cliente>/, en cualquier formato (manual en PDF, logos en AI/SVG/PNG/JPG, presentaciones, ZIP, fuentes, capturas). Saca colores, logo en blanco y tipografías sin pedirle nada técnico. Usar cuando el usuario diga "crea la marca", "usa el branding de…", "ya pegué el branding", "mi marca", o cuando un video pida una marca que aún no tiene brand.json.
---

# Marca del cliente a partir de cualquier archivo

El diseñador **solo copia el branding del cliente en `marcas/<cliente>/`**, tal como se lo dieron: sin renombrar, sin convertir y sin ordenar. Todo lo demás lo haces tú.
No le hables de JSON, roles de color, rutas ni comandos.

## 1. Localiza la carpeta
- Si no existe `marcas/<cliente>/`, créala (minúsculas y guiones) y dile: «Copia aquí todo el branding de <cliente> como te llegó y avísame».
- Si dice que el branding está en otra carpeta, como Descargas o el Escritorio, cópialo tú a `marcas/<cliente>/`.

## 2. Analiza
`PY` es `.venv\Scripts\python` en Windows y `.venv/bin/python` en Mac.
```
PY engine/run.py marca marcas/<cliente>
```
Lee la salida (también queda en `_revision/inventario.txt`) y **mira cada `_revision/hoja_*.jpg`**. Si hay texto extraído de un manual (`_revision/*_texto.txt`), léelo: los manuales suelen decir qué color es el principal y cuál el acento.

## 3. Decide tú
- **Logo:** el principal, completo y horizontal si lo hay. Mejor vectorial (SVG, PDF o AI) o un PNG grande. Evita las fotos y las páginas enteras del manual. Si el único logo está dentro de un PDF, usa la imagen extraída (`_revision/<archivo>_img*.png`).
- **Colores:**
  - `primary` es el color de marca dominante, el que más se ve y, si es posible, oscuro o medio, porque va de fondo de tarjetas y animaciones.
  - `accent` es el color vivo que contrasta con `primary`, para resaltar palabras.
  - Opcionalmente, `accent2` (segundo acento) y `light`.
  - El resto se deriva solo.
  - Prioriza los códigos escritos en documentos sobre los colores medidos en fotos. Ignora el blanco, el negro y los colores de fotos de ambiente.
- **Si el color principal es muy claro**, por ejemplo amarillo o pastel: úsalo como `accent` y pon como `primary` el color oscuro de la marca. Si no hay un oscuro, usa uno muy oscuro del mismo tono.
- **Fuentes:** si hay archivos .ttf u .otf, se detectan solos. Si el manual nombra una fuente que no está en la carpeta, dile al diseñador que, si la tiene, copie los archivos de la fuente en la carpeta. Mientras tanto se usa la fuente del sistema: Segoe UI en Windows y Arial en Mac.

## 4. Aplica
```
PY engine/run.py marca-aplicar marcas/<cliente> --logo "<archivo>" --colores primary=#xxxxxx,accent=#xxxxxx --nombre "<Nombre del cliente>"
```
- `--logo` acepta cualquier archivo de la carpeta o de `_revision/`. El fondo del logo se quita solo y se genera una versión en blanco.
- Usa `--logo-tal-cual` solo si quitar el fondo estropea el logo.
- Si avisa de poco contraste, cambia el acento.

## 5. Enséñalo y pide el visto bueno
**Mira `marcas/<cliente>/muestra.jpg`.** Comprueba:
- El logo blanco está completo, sin cajas ni restos de fondo.
- El acento se lee bien sobre el fondo.
- Los colores son los de la marca.

Si algo falla, cambia el logo o los colores y vuelve a aplicar. Después enséñale la muestra al diseñador con una frase sencilla, por ejemplo: «Así se verán las tarjetas, los rótulos y los subtítulos con la marca de <cliente>. ¿Te gusta o cambio algo?».
Si pide cambios («el naranja más oscuro», «usa el otro logo»), vuelve al paso 4.

## Si falta algo
- **Archivos que no se pueden leer** (EPS, InDesign, Figma, HEIC…): pide que los exporte a PDF, SVG o PNG.
- **No hay logo:** pídeselo en cualquier formato. Puede ser una captura de pantalla de la web del cliente.
- **No hay colores claros:** propón dos o tres combinaciones sacadas del logo y que elija.
