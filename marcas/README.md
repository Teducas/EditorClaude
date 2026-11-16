# Marcas

**Copia aquí el branding de cada cliente, en una carpeta con su nombre y tal como te llegó.** Puede ser cualquier formato: manual en PDF, logos en AI, SVG, PNG o JPG, presentaciones, un ZIP, fuentes o capturas.

```
marcas/
└─ cafe-andino/
   ├─ Manual de marca.pdf
   ├─ Logos/logo.ai
   └─ ... (lo que tengas)
```

Luego dile a Claude: *«Ya pegué el branding de Café Andino»*. Claude:
- saca los colores, el logo en blanco y las tipografías;
- te enseña una muestra para que la apruebes.

Claude genera solo los archivos `brand.json`, `logo_light.png`, `logo_color.png`, `muestra.jpg` y la carpeta `_revision/`. No hace falta tocarlos.

Solo `demo/` se sube a git. Las marcas de tus clientes se quedan en tu equipo.
