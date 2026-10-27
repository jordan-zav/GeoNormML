# Auditoría de la generación candidata

Fecha: 27 de octubre de 2026. Generación examinada: profiles_nested_v3_20261026.

**Dictamen: resultados del experimento acotado verificados; comparación completa pendiente.** No se autoriza inferir superioridad global ni promover automáticamente los pesos. Esta auditoría no reentrena modelos ni modifica el plan congelado o los resultados anteriores.

## Hallazgos

### P1. Cobertura incompleta del catálogo anterior

El catálogo define RandomForest, XGBoost y SVM_PCA, con once familias de variables. La generación ejecutó RandomForest y XGBoost, únicamente con oxides_core y combined_core. Los tres perfiles normativos fueron evaluados para combined_core. Esto equivale a ocho candidatos por dominio, no a todo el catálogo.

Quedaron fuera SVM_PCA y nueve familias: oxides, cipw, combined, oxides_contextual, combined_contextual, combined_enriched, combined_enriched_spatial, combined_enriched_geodata y combined_full. Estar definido no implica que cada conjunto sea viable: los espaciales requieren cobertura y validación de sus fuentes; los derivados de CIPW deben recalcularse con el perfil correspondiente, sin reutilizar índices históricos.

La corrección necesaria es una ejecución nueva con alcance declarado de antemano. Debe incluir SVM_PCA y registrar qué familias se prueban, cuáles se excluyen y por qué. No basta con añadir SVM al ranking final de esta ejecución: la evaluación anidada debe incluirlo desde la selección interna. El resultado de la nueva selección requerirá una evaluación externa posterior, porque los datos de desarrollo ya se inspeccionaron.

### P2. No se retaron los hiperparámetros

La lectura de los pesos oficiales anteriores y de los candidatos confirma que se conservaron los ajustes principales:

| Algoritmo | Ajustes comprobados |
| --- | --- |
| RandomForest | 400 árboles, profundidad sin límite, balanced_subsample, semilla 42, n_jobs 1 |
| XGBoost | 300 árboles, profundidad 6, tasa 0,05, subsample 0,9, colsample_bytree 0,9, hist, multi:softprob, semilla 42, n_jobs 1 |

Se compararon algoritmos y entradas con ajustes fijos. No hubo búsqueda de hiperparámetros. Cualquier búsqueda futura debe quedar dentro de los folds internos, con presupuesto y criterios fijados antes de ejecutarla.

### P2. Selección inestable y errores relevantes por clase

En volcánicas, los cinco folds externos eligieron cinco candidatos distintos: óxidos XGBoost, Verma XGBoost, óxidos RandomForest, compatibilidad RandomForest y compatibilidad XGBoost. En plutónicas, Verma XGBoost ganó dos folds; los otros tres eligieron óxidos RandomForest, Verma RandomForest y compatibilidad XGBoost.

Las métricas verificadas evalúan ese procedimiento de selección, no exclusivamente el estimador final.

| Dominio | Exactitud OOF | Macro F1 OOF | MCC OOF | Filas |
| --- | ---: | ---: | ---: | ---: |
| VOL | 0,756345 | 0,587002 | 0,633581 | 1.379 |
| PLU | 0,565553 | 0,369604 | 0,461715 | 778 |

Hay clases débiles: latita tiene sensibilidad aproximada de 0,11 sobre 19 muestras; monzodiorita, 0,07 sobre 28; monzonita, 0,08 sobre 26; tonalita, 0,09 sobre 67. Son cifras de las predicciones anidadas, con poblaciones pequeñas en algunas clases. El promedio global no acredita utilidad uniforme por litología.

### P2. Población y evaluación impiden proclamar una mejora

La comparación común usa 2.701 de los 2.755 IDs: quedan fuera de esta evaluación 39 VOL y 15 PLU por cobertura conjunta, aunque todos siguen en el registro. El control de óxidos también se restringió a esa población para comparar candidatos en igualdad de condiciones. No mide su cobertura potencial sobre toda la base.

El holdout histórico ya estaba inspeccionado y los pesos finales se reajustaron incluyendo sus muestras elegibles. No debe usarse para validar de nuevo esos pesos finales. Una comparación directa con porcentajes de otra población o protocolo no demuestra mejora ni deterioro del motor CIPW.

### P2. El congelado de configuración es parcial

El plan conserva versiones, parámetros normativos y hashes del ejecutor y selector. No congela por hash todos los módulos importados de entrenamiento, ni todos los parámetros efectivos de estimadores. La coincidencia actual con las definiciones y pesos anteriores se verificó en esta auditoría; no prueba por sí sola que cualquier entorno futuro reproduzca el entrenamiento.

Para la siguiente ejecución se deben registrar los parámetros completos de cada pipeline, las columnas y sus tipos, todos los módulos y runtime normativo relevantes, commit y estado del árbol, así como particiones internas y externas. Debe conservarse intacta la evidencia de esta ejecución.

## Comprobaciones realizadas

- Se verificaron los hashes de los 68 originales auditados y de ambos pesos candidatos.
- Se reprodujeron cobertura común, pertenencia a entrenamiento y holdout, agrupación de muestras y folds externos desde la base original.
- Se reconstruyeron los folds internos y no se detectaron grupos compartidos. No se volvieron a ajustar estimadores para reproducir sus puntuaciones internas guardadas.
- Se comprobaron las selecciones guardadas contra su criterio de ranking y las métricas externas contra todas las predicciones OOF.
- Se contrastaron clases, columnas, conteos y parámetros principales de los pesos finales con los metadatos y las definiciones actuales.
- Las pruebas previas del adaptador compararon las variables de 2.701 filas y predicciones de prueba de ambos dominios. Eso verifica compatibilidad de inferencia, no calidad predictiva externa.

La evidencia privada, incluyendo resultados por clase, está en D:\DevResources\Projects\GeoNormML\Reports\CandidateAudit\2026-10-27\audit_with_previous_parameters.json. El script reproducible es scripts/audit_candidate_generation.py; requiere --run CARPETA_DE_CANDIDATOS y --output ARCHIVO_NUEVO. Solo lee los artefactos originales y escribe la evidencia nueva; no entrena ni sustituye pesos.

Las pruebas de software y la auditoría no equivalen a un benchmark completo. El próximo paso es definir y ejecutar la comparación ampliada antes de elegir modelos para producción.
