# Scripts Legacy

Esta carpeta contiene scripts de un solo uso o utilidades auxiliares que formaron parte de etapas exploratorias, armonizaciones intermedias de datos o generación de figuras específicas en fases previas del proyecto.

Se conservan aquí como registro de procedencia y trazabilidad metodológica, pero **ya no forman parte del pipeline reproducible oficial** coordinado por [`scripts/run_pipeline.py`](../run_pipeline.py).

## Contenido

| Script | Descripción y contexto |
| --- | --- |
| `apply_reclassification_to_master.py` | Reclasificación litológica intermedia sobre `Merge_Filtered_name_normalized.xlsx` para generar la versión preliminar del master. |
| `apply_rock_type_and_cipw.py` | Cálculo normativo CIPW en lote sobre la versión preliminar del master (`v1` a `v2_cipw`). |
| `normalize_filtered_names.py` | Normalización textual de nombres litológicos y términos texturales a partir del consolidado inicial. |
| `run_cipw_from_csv.py` | Utilidad de línea de comandos para ejecutar cálculo CIPW sobre archivos CSV arbitrarios. |
| `generate_dataset_cleanup_graphic.py` | Generador puntual del gráfico de depuración de muestras con valores fijos para el tótem del póster. |
| `generate_report_confusion_matrices.py` | Generador de matrices de confusión estilizadas para el informe de contexto 2025. |
