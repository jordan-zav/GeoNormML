# Catálogo de scripts

Ejecutar desde la raíz del repositorio con el entorno del proyecto. Los nombres
y las rutas de los módulos se conservan para mantener los comandos existentes.

## Preparación y trazabilidad

| Módulo | Función |
| --- | --- |
| normalize_filtered_names | Normalización de nombres históricos |
| apply_reclassification_to_master | Aplicación de la reclasificación al maestro |
| apply_rock_type_and_cipw | Dominio de roca y resultados CIPW |
| run_cipw_from_csv | Cálculo CIPW de una tabla CSV con GeoNormPy |
| create_training_ready_dataset | Construcción de la tabla inicial de entrenamiento |
| assign_final_ids | Asignación de IDs |
| apply_quality_filter | Filtro geoquímico de la preparación histórica |
| finalize_consistent_training_dataset | Construcción de la versión v4 consistente |
| spatial_join_dataset | Enriquecimiento cartográfico y distancias |
| clean_dataset | Curación auditada; conserva los IDs de la base oficial por defecto |

Las etapas históricas pueden escribir rutas fijas de Dataset. Revisar sus
entradas y salidas antes de ejecutarlas; no son una orden de regenerar la base.

## Modelado y evaluación

| Módulo | Función |
| --- | --- |
| run_pipeline | Coordinación de las doce etapas; admite --list y --dry-run |
| build_modeling_artifacts | Particiones, manifiestos y catálogo de variables |
| run_ml_benchmark | Comparación de modelos con validación por grupos |
| validate_models | Evaluación de los dos baselines y holdout reservado |
| export_official_models | Ajuste y exportación de baselines; modelos espaciales opcionales |
| export_transfer_bundle_models | Exportación del catálogo ampliado para transferencia |

Exportar implica ajustar modelos; no valida por sí mismo su aplicación a otra
región. La validación espacial externa sigue siendo un requisito independiente.

## Figuras e interpretación

| Módulo | Función |
| --- | --- |
| generate_shap_plots | Explicación de los modelos realmente exportados |
| generate_benchmark_figures | Figuras de comparación del benchmark |
| generate_report_confusion_matrices | Matrices de confusión para informes |
| generate_tas_comparison | Comparación TAS, CIPW y litología reportada |
| generate_reliability_dashboard | Panel de evidencia de confiabilidad |
| generate_dataset_cleanup_graphic | Ilustración de la depuración |

Las explicaciones SHAP sobre muestras de entrenamiento no son métricas de
validación. Consultar la [base vigente](../docs/revisiones/curated_baseline_correction_20260920.md)
antes de reutilizar figuras históricas.
