# Comparación ampliada y recomendación por dominio

Fecha: 27 de octubre de 2026. Generación: expanded_nested_v4_20261027.

**Recomendación: conservar XGBoost como familia de referencia volcánica y RandomForest como referencia plutónica. No promover automáticamente los pesos nuevos.** La búsqueda ampliada no demuestra una mejora general de clasificación. Para ensayos con contrato normativo actualizado quedaron dos candidatos trazables, separados de los modelos vigentes.

## Qué se ejecutó

Se cubrieron las once familias de variables del catálogo y los tres algoritmos: RandomForest, XGBoost y SVM con escalado, PCA al 95 % de varianza y kernel RBF. Los tres perfiles GeoNormPy 1.1.0 fueron incluidos donde las variables dependen de normas; los índices y el contexto petroquímico se recalcularon por perfil.

Por dominio se compararon 120 configuraciones transferibles, que combinan ocho familias sin variables espaciales, los perfiles pertinentes y dos configuraciones por algoritmo. Se añadieron 27 diagnósticos espaciales: tres familias, tres perfiles y tres algoritmos en su ajuste original. Las familias espaciales no participaron en la selección principal.

| Algoritmo | Configuración original | Alternativa acotada |
| --- | --- | --- |
| RandomForest | 400 árboles, balanced_subsample, profundidad sin límite | Mínimo de 3 muestras por hoja y max_features 0,7 |
| XGBoost | 300 árboles, profundidad 6, tasa 0,05 | 400 árboles, profundidad 3, tasa 0,03 |
| SVM/PCA | C=1, gamma scale, pesos balanced | C=10, resto igual |

No es una búsqueda exhaustiva de todos los hiperparámetros posibles. El espacio, los parámetros completos de los pipelines, los hashes de código e inputs y las versiones se congelaron antes de los ajustes. La ejecución usó un máximo de dos ajustes pesados simultáneos mediante los bloqueos existentes.

Se conservaron las 2.755 muestras originales y se usaron las mismas 2.701 elegibles comunes de la comparación v3. El desarrollo contiene 1.379 VOL y 778 PLU. Se mantuvieron los cinco folds externos, con tres internos para seleccionar, y cinco folds de desarrollo para la selección final. Se ajustaron 5.112 estimadores incluyendo controles triviales; posteriormente se ajustaron diez controles de configuración vigente sobre las mismas particiones.

## Métricas externas internas por dominio

Cada fila de algoritmo representa un procedimiento que elige variables, perfil y configuración únicamente dentro del entrenamiento del fold externo. La selección general puede elegir entre los tres algoritmos. Estas cifras no son una prueba externa independiente de los pesos finales reajustados.

| Dominio | Procedimiento | Exactitud | Macro F1 | MCC |
| --- | --- | ---: | ---: | ---: |
| VOL | Selección general ampliada | 75,34 % | 0,6071 | 0,6417 |
| VOL | Solo RandomForest, selección interna | 75,49 % | 0,6229 | 0,6428 |
| VOL | Solo XGBoost, selección interna | 76,29 % | 0,6183 | 0,6466 |
| VOL | Solo SVM/PCA, selección interna | 68,96 % | 0,6197 | 0,5788 |
| VOL | Clase más frecuente | 50,11 % | 0,0742 | 0,0000 |
| PLU | Selección general ampliada | 53,86 % | 0,3932 | 0,4371 |
| PLU | Solo RandomForest, selección interna | 53,86 % | 0,3932 | 0,4371 |
| PLU | Solo XGBoost, selección interna | 54,76 % | 0,3784 | 0,4409 |
| PLU | Solo SVM/PCA, selección interna | 45,37 % | 0,3692 | 0,3603 |
| PLU | Clase más frecuente | 24,81 % | 0,0398 | 0,0000 |

## Comparación con las generaciones anteriores

Frente a la selección v3, VOL pasa de exactitud 75,63 % y macro F1 0,5870 a 75,34 % y 0,6071. PLU pasa de 56,56 % y 0,3696 a 53,86 % y 0,3932. Hay una mejora modesta de macro F1 acompañada de una pérdida de exactitud.

Las 1.999 permutaciones emparejadas de predicciones OOF, intercambiando grupos completos, dieron p exploratorio 0,4795 en VOL y 0,2725 en PLU para el contraste con v3. Ninguno respalda una diferencia clara; tampoco después de la corrección Holm de los ocho contrastes previstos. Estos valores son diagnósticos: compartir datos de entrenamiento entre folds y haber revisado experimentos previos impide tratarlos como confirmación independiente. No se permutaron filas ignorando las réplicas.

Como control descriptivo posterior, se reajustó la configuración vigente sobre las mismas muestras y folds, conservando sus variables normativas históricas:

| Dominio | Configuración vigente reajustada | Exactitud | Macro F1 | MCC |
| --- | --- | ---: | ---: | ---: |
| VOL | XGBoost, combined_core histórico | 76,94 % | 0,6338 | 0,6564 |
| PLU | RandomForest, combined_core histórico | 55,14 % | 0,3434 | 0,4430 |

Este control no es una nueva prueba ciega y no resuelve la procedencia del perfil normativo histórico, que sigue sin estar registrado. Sí muestra por qué no corresponde anunciar que la generación ampliada mejora universalmente la configuración anterior.

## Pesos seleccionados y decisión práctica

| Dominio | Selección para ajuste final | Estado recomendado |
| --- | --- | --- |
| VOL | XGBoost original, combined_contextual, Verma 2003 | Candidato actualizado para ensayos; mantener XGBoost como referencia, sin reemplazo automático de pesos |
| PLU | RandomForest regularizado, combined_contextual, Verma 2003 | Candidato si se prioriza macro F1; no hay superioridad general demostrada para sustituir pesos |

Ambos usan 41 variables: 12 óxidos y auxiliares, 27 fases y dos categorías petroquímicas derivadas. El macro F1 y la exactitud de la tabla evalúan procedimientos de selección, no exclusivamente estas dos configuraciones finales. Los pesos se reajustaron sobre todas las muestras elegibles del dominio y por eso necesitan nuevos datos para su evaluación independiente.

En los cinco folds plutónicos se eligió RandomForest regularizado, con distintas familias y perfiles. En volcánicas se eligió cuatro veces RandomForest regularizado y una vez XGBoost. No se estabiliza un perfil normativo único entre folds. Que Verma resulte seleccionado en ambos ajustes finales no demuestra superioridad petrológica de ese perfil.

En PLU persisten sensibilidades bajas, por ejemplo monzonita cercana a 0,08 y tonalita cercana a 0,13. Ampliar la búsqueda no resolvió la separación de todas las litologías. No corresponde elegir retrospectivamente un algoritmo según el nombre verdadero de la roca que se pretende predecir.

La comparación no modifica los modelos predeterminados de PetroPyQAPF. Estos pesos v4 todavía requieren un adaptador y paquete de distribución propios; no se ha probado su ejecución mediante la API de PetroPyQAPF. Sí se comprobaron sus hashes, clases, predicciones y normalización de probabilidades sobre las matrices de variables reconstruidas. Esto no equivale a calibrar probabilidades ni validar con datos externos.

## Resultado espacial: prometedor, separado

El mejor resultado descriptivo observado entre los 27 diagnósticos fue combined_full con XGBoost y Verma: VOL, exactitud 79,55 % y macro F1 0,7077; PLU, 61,18 % y 0,5080. Esa elección se hace después de inspeccionar resultados y no tiene una evaluación externa adicional.

La geología y ubicación aportan señal, pero agrupar réplicas no impide compartir contexto regional entre entrenamiento y evaluación. Estas cifras no justifican adoptar el modelo espacial como clasificador geoquímico general. Su siguiente evaluación debe bloquear regiones, campañas o unidades pertinentes y separar los datos usados para seleccionar del examen final.

## Límites y reproducibilidad

- F y Cl están completamente ausentes en la base; incluir sus columnas no valida su efecto real.
- Las series Alcalina/Subalcalina usadas como contexto son heurísticas derivadas de química y normas, no etiquetas independientes de afinidad. La recomendación solicitada es por dominio.
- Las normas son transformaciones de la química; no incorporan por sí mismas una observación petrográfica independiente.
- El protocolo se amplió después de inspeccionar v3. La evidencia sigue siendo interna y exploratoria, aunque cada ajuste respete la separación entre entrenamiento y evaluación.
- No se eliminaron muestras originales, no se sobrescribieron pesos vigentes y se verificó que los 68 archivos originales auditados permanecen intactos.

Los pesos, plan completo, puntos de reanudación y predicciones privadas están en D:\DevResources\Projects\GeoNormML\CandidateModels\expanded_nested_v4_20261027. La revisión independiente y controles están en D:\DevResources\Projects\GeoNormML\Reports\ExpandedRuns\review_20261027.json. Datos y pesos no se suben al repositorio.

Scripts: inspect_expanded_inputs para cobertura; build_expanded_models.ps1 para recursos y bloqueos; train_expanded_generation para entrenamiento aislado, con --resume sujeto a hashes y configuración; review_expanded_generation para verificar evidencia y calcular el control vigente emparejado. Usar siempre un destino nuevo para nuevas ejecuciones y revisiones.

Referencias metodológicas: [validación anidada](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html) y [validación con grupos](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data). El intercambio emparejado de predicciones de este experimento es un diagnóstico propio descrito arriba; no se presenta como el test de permutación de etiquetas de scikit-learn.
