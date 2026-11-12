# Editor de video Claude → CapCut

Repositorio para editar videos de una persona hablando a cámara y entregar un proyecto editable de CapCut Desktop (Windows).

- Para cualquier pedido de edición de video sigue la skill `.claude/skills/editar-video-capcut/SKILL.md`.
- Ejecuta todo con `.venv\Scripts\python engine\run.py ...` desde la raíz. Si falta `.venv`, corre `setup.ps1`.
- Cada video vive en `projects/<video>/` (ignorado por git). Las marcas en `brands/<marca>/` (solo `demo` se sube).
- `examples/ramon-video1/` es un montaje real completo: úsalo como referencia de criterio y de código para las escenas.
- `engine/` es el motor reutilizable; si cambias su comportamiento, mantén compatible el formato de `project.json`.
- Habla con el usuario en español.
