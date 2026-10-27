# Integración GeoNormML de PC y laptop

Fecha: 26 de octubre de 2026.

Se integran la rama PC 8824c7b y la rama laptop 50bf87f sobre la limpieza de
main 1e47623. Las dos ramas originales se conservan para recuperar su evidencia.

## Decisiones de integración

- La corrección ID_Final int64, el núcleo ML y sus pruebas eran iguales en
  ambas ramas. Se conservan sin reinterpretar la base ni reentrenar.
- Se incorporan los dos scripts de comparación CIPW de la laptop. Su ejecución
  es explícita y requiere los datos y modelos locales; no forman parte de una
  comprobación documental ni se ejecutan al instalar.
- README.md permanece en inglés y README.es.md en español, con enlaces de idioma.
  Se conserva la sección de fuentes y se distinguen las rutas de entorno por PC.
- Los documentos se organizan en metodologia, revisiones, informes y publicaciones.
  Se retiran las copias raíz redundantes; la trazabilidad académica duplicada se
  remite a dataset_traceability.md. El historial conserva los textos anteriores.
- Se usan las imágenes ya versionadas en docs con nombres normalizados, según
  main y la laptop. Los pósteres utilizan esas rutas y salidas configurables.
- No se reincorporan DOCX, PDF, PPTX ni previsualizaciones que main había retirado.
  El material local de la PC se preserva por separado antes de actualizar el clon.
- scripts/legacy mantiene las utilidades históricas; el catálogo no las presenta
  como módulos activos en la raíz de scripts.

## Corrección del informe CIPW

El comparador registra por separado unsupported y error. El generador de
figuras solo sumaba error, por lo que podía omitir entradas fuera del alcance
del perfil en el gráfico y la tabla. Ahora agrupa ambos estados sin perder
filas, comprueba que el total represente la población e impide descartar estados
desconocidos. Las pruebas usan recuentos sintéticos, no métricas nuevas de roca.

El informe requiere un directorio explícito y solo se ejecuta mediante su
función principal. Consultar --help o importar sus utilidades no lee bases ni
modelos ni genera productos. Su narrativa es histórica, del experimento del
26 de octubre con 2.755 filas y 2.701 comunes, y no se presenta como generador
de conclusiones para experimentos arbitrarios.

## Alcance de las comprobaciones

Se ejecutaron 40 pruebas correctas, Ruff sin incidencias y pip check sin
conflictos. Se verificaron 45 referencias locales sin destinos ausentes.
No se ejecuta compare_cipw_profiles sobre la base oficial ni se recalculan las
métricas de la laptop. Dataset, artifacts, modelos y credenciales quedan fuera
del commit. La validación de software no demuestra superioridad predictiva ni
transferencia geográfica.
