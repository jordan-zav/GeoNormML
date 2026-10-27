# Catálogo de scripts

audit_candidate_generation verifica una ejecución existente sin entrenar:
hashes, población, grupos, métricas OOF, selecciones, pesos y parámetros anteriores.
Escribe evidencia en un archivo nuevo e informa las opciones del catálogo que
no se ejecutaron. No confundir comprobación de resultados con benchmark completo.

train_candidate_generation compara tres perfiles normativos y controles de óxidos
mediante selección anidada por grupos. Escribe únicamente una carpeta nueva de
candidatos; no sustituye los modelos vigentes. prepare_candidate_transfer genera
el contrato de integración y verifica su reproducción con --check. Consulte el
[protocolo y sus límites](../docs/revisiones/generacion_candidata_v3_20261026.md).

audit_metric_protocols compara CV por filas y por grupos sobre entrenamiento y
base completa, con los mismos óxidos, normas e hiperparámetros. Ajusta modelos
temporales de diagnóstico; no los exporta ni modifica los artefactos vigentes.
Los escenarios completos reutilizan el holdout y no son una nueva validación independiente.

reconcile_publication verifica hashes de base y validación, contrasta las
predicciones del holdout y produce un snapshot nuevo para publicación.
No entrena ni sustituye modelos. Las identidades Legacy y vigente se describen
en [la decisión de versiones](../docs/revisiones/modelos_legacy_y_vigentes.md).

Ejecutar desde la raíz del repositorio con el entorno del proyecto. Los nombres
y las rutas de los módulos se conservan para mantener los comandos existentes.

## Preparación y trazabilidad

| Módulo | Función |
| --- | --- |
| legacy/normalize_filtered_names | Normalización de nombres históricos |
| legacy/apply_reclassification_to_master | Aplicación de la reclasificación al maestro |
| legacy/apply_rock_type_and_cipw | Dominio de roca y resultados CIPW |
| legacy/run_cipw_from_csv | Cálculo CIPW de una tabla CSV con GeoNormPy |
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
| legacy/generate_report_confusion_matrices | Matrices de confusión para informes |
| generate_tas_comparison | Comparación TAS, CIPW y litología reportada |
| generate_reliability_dashboard | Panel de evidencia de confiabilidad |
| legacy/generate_dataset_cleanup_graphic | Ilustración de la depuración |

Las explicaciones SHAP sobre muestras de entrenamiento no son métricas de
validación. Consultar la [base vigente](../docs/revisiones/curated_baseline_correction_20260920.md)
antes de reutilizar figuras históricas.

## Comparación de perfiles CIPW

- compare_cipw_profiles: experimento explícito que recalcula normas y ajusta
  estimadores clonados; exige motor fuente y salida nueva. No sustituye modelos.
- report_cipw_profile_comparison: verificación de predicciones e informe
  histórico del experimento fechado; exige --output. No es un generador de
  conclusiones para una base o evaluación distinta.

Estos scripts no se ejecutan durante una revisión documental. Usa --help para
consultar argumentos sin iniciar el experimento. Los scripts de legacy no son
etapas activas del pipeline; consulta [su alcance](legacy/README.md).
