# Sistema de pósteres — XXIII Congreso Peruano de Geología

Plantilla parametrizable para una serie de pósteres verticales de `1080 × 1920 px`
(`19.05 × 33.86 cm` a 144 dpi). El generador crea un PPTX de hasta diez páginas
por trabajo, con todos los textos, imágenes y métricas definidos en JSON; no hay
contenido científico codificado en el layout.

## Sistema visual

- Fuente: Arial. Cuerpo y pie: 12 pt; subtítulos: 13 pt; título: 14 pt.
- Paleta compartida: azul UNI `#003B70`, celeste `#00A6CE`, tinta `#15202B`,
  fondo `#F5F8FA`, acento mineralógico `#D98324`.
- Grid: márgenes de 54 px, tres columnas de 288 px y gutters de 36 px.
- Las figuras se presentan en tarjetas blancas, con borde celeste y pie de 12 pt.
- Los recuadros de logo UNI y SGP/CPG siempre se sitúan en la misma coordenada.

## Uso

1. Copia una configuración de `configs/` y reemplaza únicamente el contenido y
   las rutas de `visual` por evidencia real.
2. Ejecuta `python build_poster.py configs/<trabajo>.json`.
3. Revisa el PPTX generado y, cuando el contenido esté aprobado, expórtalo desde
   PowerPoint a PDF. El PDF no se genera antes de la aprobación editorial.

Las rutas `visual` pueden ser PNG, JPG o SVG convertidos previamente a PNG. Si la
ruta no existe, el generador dibuja una alerta visible: así nunca se reemplaza
evidencia faltante por un mockup o por datos inventados.

## Estructura de cada configuración

Cada entrada de `slides` define una pantalla. Las claves disponibles son
`kind` (`title`, `context`, `method`, `results`, `conclusions`), `heading`,
`body`, `bullets`, `visuals` y `metrics`. Los diez slots propuestos priorizan
metodología y resultados; pueden reducirse, pero no ampliarse por encima de 10.

