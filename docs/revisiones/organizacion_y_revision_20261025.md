# Organización y revisión del 25 de octubre de 2026

## Cambios realizados

- Se agruparon 21 documentos en metodologia, revisiones, informes, publicaciones
  y figuras. Se verificó que sus contenidos conservan los hashes anteriores.
- Se añadieron un índice de documentación, una guía de trabajo y un catálogo
  de los scripts. Se actualizaron las rutas de README, AGENTS y los pósteres.
- Se conservó el bloque local preexistente de AGENTS; solo se actualizó su
  referencia al documento trasladado.
- Los IDs de la curación usan int64 explícito. En el Python global de Windows,
  la conversión anterior a int producía índices int32 y fallaba la comparación
  con una referencia de Excel int64, aunque los valores fueran idénticos.
  La prueba original reproducía el fallo; ahora pasa. Se añadieron controles
  de tipo portable y rechazo de mediciones cambiadas.
- Se preparó un entorno aislado en D:\DevResources\Projects\GeoNormML-11cc092a72\.venv,
  instalado desde requirements.txt y las restricciones científicas existentes.
- Los tótems Python e Illustrator resuelven sus imágenes en docs/figuras y
  usan salidas locales configurables, en lugar de escribir por defecto en I:.
  Se declaró el extra posters para las dependencias Python de presentaciones.
- Se corrigió la descripción del preprocesador: las categorías faltantes usan
  una etiqueta explícita, conforme al código, y no la categoría más frecuente.

## Comprobaciones

| Control | Resultado |
| --- | --- |
| Pruebas automáticas en el entorno aislado | 32 correctas |
| Ruff en src, scripts y tests | Sin incidencias |
| pip check en el entorno aislado | Sin conflictos |
| Sintaxis de archivos Python | 39 archivos analizados |
| Base oficial | 2.755 IDs únicos; 1.764 VOL y 991 PLU |
| Base frente al manifiesto | SHA-256 coincidente |
| Referencia v4 | IDs y valores originales coincidentes |
| Datos y resultados locales | 68 archivos con contenido e inventario conservados |
| Documentos trasladados | 21 hashes conservados |
| Enlaces relativos antes de añadir este informe | 32 comprobados |
| Holdout guardado | 553 muestras; sin grupos compartidos con entrenamiento |
| CV guardada | Cinco pliegues por dominio, diez en total; sin grupos compartidos entre train y validación |
| CLI del pipeline | Lista y simulación de las etapas 6 a 12 correctas |

Los manifiestos de validación, exportación oficial y esquema de transferencia
identifican el mismo hash de la base oficial. No se cargaron los modelos
serializados ni se recalcularon sus predicciones. Las pruebas usan ejemplos
sintéticos; no representan un nuevo entrenamiento científico.

## Hallazgos que deben conocerse

El Python global tenía scikit-learn 1.8.0, fuera del intervalo del proyecto,
no tenía SHAP y presentaba cuatro conflictos de dependencias de otras
aplicaciones. No se alteró ese entorno; el aislado usa las versiones declaradas.

El informe histórico de agosto utiliza 2.887 filas y considera oficiales
modelos espaciales. La corrección posterior de septiembre mantiene 2.755
muestras y trata los modelos espaciales como experimentales. No reutilizar
las conclusiones antiguas sin contrastarlas con esa corrección y los manifiestos.

El borrador paper_geonormpy_geonormml_cpg.md está vacío. Se conserva como estaba;
el borrador cpg_xxiii tiene contenido. Los enlaces absolutos antiguos a Google
Drive son referencias históricas y no se han validado como rutas disponibles
en esta PC. Los generadores de pósteres conservan contenido editorial histórico
que debe revisarse antes de publicar.

Las etapas antiguas de preparación usan salidas fijas y pueden escribir tablas
locales. El pipeline completo y los exportadores entrenan o reemplazan salidas;
no se ejecutaron durante esta revisión. Tampoco se generaron pósteres, se abrió
Illustrator, se migraron bases, se eliminaron archivos o se publicaron cambios.

## Evidencia local

Los inventarios de conservación, los traslados y el resultado de la comprobación
están en O:\0. Projects\RepoSyncLogs, con prefijo geonormml y fecha 20261025.
La [guía de trabajo](../GUIA_DE_TRABAJO.md) contiene los comandos para validar
el proyecto con su entorno aislado.
