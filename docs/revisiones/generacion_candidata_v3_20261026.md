# Generación candidata para PetroPyQAPF

Revisión cerrada el 27 de octubre de 2026. Identificador: profiles_nested_v3_20261026.
Estado: candidate_internal_validation_external_pending. Los modelos vigentes y Legacy se conservan; esta generación no constituye una promoción a producción.

La [auditoría posterior](auditoria_candidatos_20261027.md) confirma las métricas y
precisa el alcance incompleto: faltaron SVM_PCA y nueve familias del catálogo.
No hubo optimización de hiperparámetros y la selección varió entre folds.

## Protocolo y cobertura

Se conservaron los 2.755 identificadores de la base curada. Se recalcularon los perfiles extended_cipw_v3, verma2003 y pruseth2009 con GeoNormPy 1.1.0. La comparación utiliza las 2.701 muestras elegibles comunes: 1.725 volcánicas y 976 plutónicas. Las restantes figuran en el registro de cobertura; no se borraron ni reclasificaron.

Se compararon ocho candidatos por dominio: RandomForest y XGBoost con óxidos, y ambos algoritmos con óxidos más normas de cada uno de los tres perfiles. Se conservaron los hiperparámetros fijados, sin búsqueda adicional. La selección usa macro F1 de predicciones fuera de fold, seguida de MCC, exactitud, menor número de variables y orden predefinido de candidatos.

La evaluación anidada usa cinco folds externos y tres internos, agrupando réplicas. La imputación se ajusta dentro de cada entrenamiento. La selección final usa cinco folds sobre la partición de desarrollo. Se realizaron 334 ajustes. El conjunto histórico de prueba no participa en la selección, pero ya había sido inspeccionado: sus métricas son descriptivas y no representan una nueva prueba ciega.

## Resultados

| Dominio | Modelo seleccionado para el ajuste final | Variables | n desarrollo | Exactitud anidada | Macro F1 anidado | MCC anidado |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Volcánico | RandomForest | 12, óxidos y auxiliares | 1.379 | 0,756345 | 0,587002 | 0,633581 |
| Plutónico | XGBoost, Verma 2003 | 39, óxidos y normas | 778 | 0,565553 | 0,369604 | 0,461715 |

Estas métricas externas evalúan el procedimiento de selección: cada fold externo puede elegir otro candidato. No son una evaluación independiente del archivo final reajustado. Los modelos finales se ajustaron con toda la población elegible de su dominio.

En el conjunto histórico descriptivo, el modelo volcánico obtuvo exactitud 0,763006 y macro F1 0,717877 sobre 346 muestras; el plutónico, exactitud 0,540404 y macro F1 0,356545 sobre 198. El resultado plutónico no justifica reemplazar automáticamente el modelo vigente. Verma y Pruseth empataron en la selección final plutónica; el orden predefinido resolvió el empate, sin demostrar superioridad científica de Verma.

## Crítica y límites

No se demuestra una mejora general frente a generaciones anteriores: cambian la población elegible y el protocolo de evaluación. Agrupar réplicas tampoco equivale a validar en otra región, campaña o laboratorio. La baja macro F1 plutónica exige examinar clases minoritarias y obtener una validación externa antes de promover los modelos. No deben interpretarse las probabilidades como incertidumbre calibrada.

La fracción férrica atómica fija de 0,15 y la asignación de carbonato a calcita son supuestos explícitos del contrato normativo, no mediciones petrográficas. Se exigen diez óxidos mayores medidos; los componentes normativos opcionales ausentes se omiten. Ap reúne Ap y FAp. LOI y Sum_Oxs conservan sus valores reportados; sus ausencias se imputan con parámetros aprendidos. Un LOI negativo finito se conserva como posible ganancia de masa.

## Reproducibilidad e integración

El plan se congeló antes del entrenamiento. Su SHA-256 es 5b3d804497298168ae80849aad789393b87c9625bfe54386079b12e6f09f9bad. La revisión independiente recalculó las métricas, comprobó la separación de grupos y verificó que los 68 archivos originales auditados no cambiaron.

Los resultados y pesos privados están en D:\DevResources\Projects\GeoNormML\CandidateModels\profiles_nested_v3_20261026. No se incorporan al repositorio datos, pesos ni credenciales.

- scripts/train_candidate_generation.py --output CARPETA_NUEVA genera una ejecución sin sobrescribir resultados.
- scripts/prepare_candidate_transfer.py --run CARPETA prepara el esquema de transferencia; --check comprueba su reproducción.
- tests/test_candidate_generation.py verifica que la selección interna no acceda a las filas externas y que los desempates sean deterministas.
- El adaptador de PetroPyQAPF comparó sus variables con las del entrenamiento en las 2.701 muestras elegibles. Las pruebas privadas verifican también predicciones, metadatos y API de análisis con LOI ausente y negativo.

La transferencia conserva el cifrado previsto para distribución. No se generó un instalador ni se sustituyó el paquete predeterminado de PetroPyQAPF en esta revisión.
