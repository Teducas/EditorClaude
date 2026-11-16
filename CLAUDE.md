# Editor de video Claude → CapCut

Repositorio para editar videos de una persona hablando a cámara y entregar un proyecto editable de CapCut Desktop (Windows).

- **Si el usuario escribe «INSTALAR»** (o «instálalo», «instala todo»), sigue `.claude/skills/instalar/SKILL.md` e instala todo tú, de principio a fin, sin pedirle que ejecute comandos.
- Para cualquier pedido de edición de video sigue la skill `.claude/skills/editar-video-capcut/SKILL.md`.
- **Marcas:** el diseñador solo copia el branding del cliente en `marcas/<cliente>/`, en cualquier formato. Tú lo conviertes en marca siguiendo `.claude/skills/marca/SKILL.md`. Nunca le pidas que edite JSON ni que convierta archivos.
- Ejecuta todo con `.venv\Scripts\python engine\run.py ...` desde la raíz. Si falta `.venv` o `doctor` falla, sigue primero la skill `instalar`.
- Cada video vive en `projects/<video>/` (ignorado por git). Las marcas, en `marcas/<cliente>/` (solo `demo` se sube; `brands/` se sigue leyendo por compatibilidad).
- `examples/ramon-video1/` es un montaje real completo: úsalo como referencia de criterio y de código para las escenas.
- `engine/` es el motor reutilizable; si cambias su comportamiento, mantén compatible el formato de `project.json`.
- Habla con el usuario en español.
