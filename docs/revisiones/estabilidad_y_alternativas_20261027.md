# Alternativas y sensibilidad a las particiones

Fecha: 27 de octubre de 2026. Generación: partition_stability_v5_20261027.

**Resultado:** ExtraTrees alcanza el mayor macro F1 medio entre las siete familias probadas; HistGradientBoosting queda cerca en volcánicas. Las diferencias son pequeñas frente a la variación entre repartos y el diagnóstico geográfico es débil. Los pesos nuevos siguen experimentales; no se cambian los modelos predeterminados de PetroPyQAPF ni se declara una prueba externa nueva.

## Alcance y decisiones fijadas

Se probaron RandomForest, XGBoost, SVM, ExtraTrees, HistGradientBoosting, CatBoost y regresión logística, con 34 configuraciones por búsqueda. Incluyen cambios de profundidad, tamaño de hoja, variables por división, regularización, pesos de clase, C y gamma de SVM, y uso o ausencia de PCA. Todos los parámetros efectivos y las versiones se congelaron antes de ajustar modelos.

La ronda concentra las representaciones en oxides_core y combined_contextual con Verma 2003, seleccionadas después de la exploración v4. No cruza todos los perfiles y familias con cada algoritmo nuevo. La [ronda v4](comparacion_ampliada_20261027.md) conserva su comparación del catálogo anterior completo. Ambas reutilizan datos ya revisados y son exploratorias.

| Decisión | Tratamiento |
| --- | --- |
| Base | Se conservan 2.755 IDs; comparación sobre las mismas 2.701 muestras elegibles comunes |
| Desarrollo | 1.379 VOL y 778 PLU |
| Prueba histórica | 346 VOL y 198 PLU, fuera de toda selección; ya inspeccionada anteriormente |
| Evaluación principal | Cinco folds externos, semillas 42, 137 y 2026 |
| Selección interna | Tres folds por grupos; semilla externa + 10000 + número del fold |
| Sensibilidad al número de folds | Tres folds externos, semilla 42; tres internos |
| Semilla del estimador | Siempre 42, para separar el efecto del reparto |
| Selección final | Cinco folds de desarrollo, semilla 42; después reajuste sobre todos los elegibles del dominio |
| Criterio | Macro F1 OOF; desempates por MCC, exactitud, menos variables y orden fijado |

Con cinco folds externos se entrena aproximadamente con el 80 % del desarrollo; con tres, con el 67 %. Los ajustes internos usan aproximadamente dos tercios del entrenamiento externo. No se movieron muestras históricas a la selección para buscar mejores cifras. No se probó variar los tres folds internos ni la semilla del estimador.

Las réplicas permanecen juntas por identidad de laboratorio, química principal idéntica y agrupaciones previas. Imputación, escalado y PCA se ajustan dentro del entrenamiento correspondiente. Los pesos de clase se calculan con sus etiquetas de entrenamiento. CatBoost usa categorías nativas y valores numéricos ausentes. HistGB tiene desactivada su validación aleatoria interna; SVM no calcula probabilidades, cuya calibración requiere otro protocolo por grupos.

Se realizaron 4.416 ajustes principales, incluidos controles y diagnóstico geográfico. La revisión añadió 42 controles emparejados y dos ajustes de candidatos por familia. Se reutilizó el entorno en D:\DevResources, con máximo dos ajustes pesados simultáneos. CatBoost 1.2.10 se añadió como dependencia opcional de investigación, sin cambiar las dependencias base fijadas.

## Media de las tres semillas con cinco folds

Cada familia selecciona configuración y representación usando solamente sus folds internos. Las cifras evalúan ese procedimiento, no una configuración única reajustada. Las desviaciones entre repartos son descriptivas: se reutilizan las mismas muestras; no son cohortes independientes ni intervalos de confianza.

| Familia o control | VOL exactitud | VOL macro F1 ± desviación | PLU exactitud | PLU macro F1 ± desviación |
| --- | ---: | ---: | ---: | ---: |
| RandomForest | 75,03 % | 0,6327 ± 0,0076 | 53,30 % | 0,3889 ± 0,0090 |
| XGBoost | 72,83 % | 0,6200 ± 0,0183 | 49,83 % | 0,3824 ± 0,0184 |
| SVM | 69,01 % | 0,6085 ± 0,0083 | 46,62 % | 0,3756 ± 0,0098 |
| ExtraTrees | 74,91 % | 0,6480 ± 0,0152 | 53,21 % | 0,3990 ± 0,0074 |
| HistGradientBoosting | 75,34 % | 0,6444 ± 0,0171 | 52,87 % | 0,3705 ± 0,0031 |
| CatBoost | 74,33 % | 0,6342 ± 0,0251 | 49,36 % | 0,3726 ± 0,0064 |
| Regresión logística | 63,74 % | 0,5267 ± 0,0107 | 40,23 % | 0,3435 ± 0,0118 |
| Control histórico reajustado | 76,07 % | 0,6259 ± 0,0077 | 54,97 % | 0,3426 ± 0,0065 |
| Configuración final v4 reajustada | 76,12 % | 0,6315 ± 0,0153 | 53,77 % | 0,4010 ± 0,0137 |

Los controles tienen historial de selección sobre esta base. La procedencia del perfil normativo histórico sigue sin estar registrada. La configuración final v4 se eligió previamente con los mismos datos y no constituye una alternativa independiente sin sesgo de selección.

No hay ganador universal: ExtraTrees es primero por macro F1 medio, pero supera a HistGB en VOL solo por 0,0036, frente a desviaciones de aproximadamente 0,015–0,017. El control histórico mantiene mayor exactitud media. Elegir únicamente la mejor semilla de CatBoost habría exagerado su rendimiento.

## Sensibilidad: tres frente a cinco folds externos

Misma semilla 42 y tres folds internos:

| Dominio | Procedimiento | Macro F1, cinco folds | Macro F1, tres folds |
| --- | --- | ---: | ---: |
| VOL | Selección general | 0,6166 | 0,6304 |
| VOL | ExtraTrees | 0,6342 | 0,6547 |
| VOL | HistGB | 0,6641 | 0,6446 |
| VOL | RandomForest | 0,6263 | 0,6456 |
| PLU | Selección general | 0,3806 | 0,3557 |
| PLU | ExtraTrees | 0,4074 | 0,4279 |
| PLU | HistGB | 0,3684 | 0,3298 |
| PLU | RandomForest | 0,3879 | 0,3780 |

Cambiar el número de folds también cambia la cantidad de entrenamiento y la distribución de clases. No favorece uniformemente a todos los modelos y no se eligió el reparto con la cifra mayor.

## Diagnóstico geográfico emparejado

Se usaron bloques de dos grados, unidos cuando una réplica cruzaba sus límites. Se evaluaron configuraciones fijas de óxidos, sin ajustar sus hiperparámetros con los bloques evaluados. Después se entrenaron esas mismas configuraciones en tres folds por réplicas y con la misma cobertura de coordenadas.

| Dominio | Configuración fija de óxidos | Macro F1, réplicas | Macro F1, geografía |
| --- | --- | ---: | ---: |
| VOL | RF de referencia | 0,6543 | 0,3406 |
| VOL | ExtraTrees, hoja mínima 1 | 0,6022 | 0,3226 |
| VOL | HistGB equilibrado | 0,6419 | 0,3486 |
| VOL | CatBoost equilibrado | 0,5769 | 0,3838 |
| PLU | RF de referencia | 0,3598 | 0,2575 |
| PLU | ExtraTrees, hoja mínima 1 | 0,3646 | 0,2338 |
| PLU | HistGB equilibrado | 0,3406 | 0,2058 |
| PLU | CatBoost equilibrado | 0,3698 | 0,2226 |

Este diagnóstico muestra fragilidad, pero no aísla causalmente el efecto de la geografía ni es una validación espacial robusta. Los tamaños son muy desiguales:

- VOL: 16 bloques conectados, 1.379 filas; entrenamiento/evaluación 619/760, 1.338/41 y 801/578. El tercer fold contiene 25 benmoreitas cuya clase no aparece en entrenamiento.
- PLU: 15 bloques conectados, 778 filas; tamaños 342/436, 545/233 y 669/109. Todas las clases aparecen en cada entrenamiento.

No faltan coordenadas en esas poblaciones. Cambian conjuntamente región, distribución de clases y cantidad de entrenamiento; las celdas adyacentes tampoco garantizan independencia geológica. No se debe presentar el resultado como prueba externa nacional ni atribuir toda la caída exclusivamente a ubicación. Se requieren campañas o regiones independientes y un diseño de evaluación adecuado.

## Recomendación y pesos

La regla fijada antes de entrenar seleccionó HistGB con óxidos para VOL: máximo 15 hojas, mínimo 10 muestras por hoja, L2=1 y pesos equilibrados. Para PLU seleccionó RF con contexto Verma: 400 árboles, mínimo 3 muestras por hoja, max_features=0,7 y balanced_subsample.

La selección final usa otra evaluación interna sobre todo el desarrollo; no tiene por qué coincidir con la familia de mayor promedio en los repartos externos. Su puntuación de selección no es una evaluación independiente del peso final.

Para la siguiente validación por dominio priorizaría HistGB en VOL y RF regularizado en PLU, manteniendo ExtraTrees como competidor explícito en ambos. Si se decide solo por macro F1 medio observado, ExtraTrees es primero. Las diferencias no justifican superioridad definitiva ni transferencia regional; PLU sigue especialmente limitado.

Además de los dos pesos principales, se ajustaron dos candidatos ExtraTrees usando la mejor configuración final de esa familia, ambos con contexto Verma y hoja mínima 3. La elección de familia se hizo después de comparar resultados y se etiqueta post-hoc. Ninguno de estos cuatro pesos se ha activado o probado mediante la API de PetroPyQAPF; necesitan su contrato de integración y distribución. No se declara calibración de probabilidades.

## Evidencia y reproducción

La revisión reprodujo particiones desde sus semillas, comprobó ausencia de réplicas compartidas y recalculó las puntuaciones internas y externas con las funciones de scikit-learn. Se verificaron los hashes de los 68 originales, código congelado, inputs y pesos. Los originales permanecen intactos. Las predicciones internas se conservan para auditar sin repetir todos los ajustes.

- Principal: D:\DevResources\Projects\GeoNormML\CandidateModels\partition_stability_v5_20261027.
- Revisión, candidatos de familia y figuras PNG/SVG: D:\DevResources\Projects\GeoNormML\Reports\StabilityRuns\review_20261027.
- La figura stability_macro_f1 resalta en rojo el mayor promedio entre familias, sin indicar significancia estadística.
- Pruebas locales: 83 aprobadas, incluyendo CatBoost y auditorías opcionales de datos. Ruff y pip check correctos.
- Datos, coordenadas, predicciones individuales y pesos permanecen fuera de Git.

Usar el entorno existente y constraints-research-py311.txt para dependencias opcionales. scripts/build_stability_models.ps1 gestiona turnos y lanzador; -Resume exige el mismo código, inputs, configuración y dependencias. Un experimento diferente requiere carpeta de salida y plan nuevos. scripts/review_stability_generation.py verifica evidencia y ajusta los controles adicionales en un destino nuevo.

Referencias de algoritmos: [ExtraTrees](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.ExtraTreesClassifier.html), [HistGradientBoosting](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html), [CatBoost](https://catboost.ai/docs/en/concepts/python-reference_catboostclassifier). Las métricas anteriores proceden de la ejecución local.
