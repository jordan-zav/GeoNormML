# GeoNormML y GeoNormPy: clasificación reproducible de rocas ígneas del Perú

## Estado actualizado al 14 de agosto de 2026

## Resumen ejecutivo

GeoNormML y GeoNormPy conforman una cadena reproducible para preparar datos litogeoquímicos, calcular mineralogía normativa CIPW, entrenar clasificadores supervisados y transferir modelos a PetroPyQAPF. El estado actual supera el flujo descrito en el informe de mayo de 2026: el dataset oficial pasó a la versión espacial v5, aumentó a 2887 muestras y el sistema productivo quedó organizado en cuatro modelos, con rutas distintas según la disponibilidad de coordenadas.

El sistema mantiene dos dominios separados: volcánicas, con 1821 muestras y 9 clases, y plutónicas, con 1066 muestras y 10 clases. Para cada dominio existe un baseline geoquímico aplicable sin coordenadas y un modelo espacio-contextual aplicable cuando se dispone de longitud y latitud.

Los modelos espacio-contextuales son los de mayor desempeño: XGBoost alcanza una exactitud de 82.81 por ciento en volcánicas y 65.67 por ciento en plutónicas. Estos modelos incorporan química mayor, norma CIPW, siete índices petrológicos, latitud y distancia a la fosa. No usan unidad geológica, cinturón metalogenético ni zona UTM, porque esas variables introducen dependencia regional y riesgo de fuga de información.

El paquete de transferencia a PetroPyQAPF contiene los cuatro modelos oficiales, manifiestos, esquemas, documentación y un predictor de referencia con enrutamiento automático. Por tanto, la transferencia técnica está preparada; lo pendiente es completar la validación externa independiente y verificar la integración dentro de la aplicación receptora.

## 1. Objetivo

El proyecto busca clasificar rocas ígneas mediante un flujo científico auditable que combine:

- Curación y normalización del dataset.
- Control de calidad geoquímico separado del target.
- Cálculo local de mineralogía normativa CIPW con GeoNormPy.
- Definición explícita de conjuntos de variables.
- Comparación reproducible de RandomForest, SVM con PCA y XGBoost.
- Selección de modelos por dominio litológico y contexto de entrada.
- Exportación de artefactos utilizables por PetroPyQAPF.

## 2. Evolución respecto del proyecto 2025-II

El trabajo original demostraba la utilidad de combinar geoquímica, norma CIPW y aprendizaje supervisado, pero dependía de hojas de cálculo, ShinyNORRRM y Orange Data Mining. La reconstrucción actual consolida la lógica en Python y deja trazabilidad de datasets, variables, métricas, divisiones, modelos y reglas de transferencia.

Los cambios principales son:

- GeoNormPy reemplaza la dependencia operativa de ShinyNORRRM.
- El benchmark se ejecuta de forma reproducible con validación cruzada estratificada de 5 pliegues.
- El target litológico se normalizó y se redujo a clases con soporte utilizable.
- Las variables de control, las variables poco completas y las variables con riesgo de fuga se separaron de los modelos oficiales.
- Se incorporó contexto espacial regional mediante latitud y distancia a la fosa.
- El sistema pasó de dos a cuatro modelos oficiales para admitir inferencia con y sin coordenadas.

## 3. Dataset oficial

Archivo vigente:

Dataset/Filtered/final/Merge_Filtered_training_ready_v5_spatial.xlsx

Hoja de trabajo:

training_ready_final

| Propiedad | Valor |
|---|---:|
| Muestras totales | 2887 |
| Clases litológicas | 19 |
| Entrenamiento del holdout | 2309 |
| Prueba del holdout | 578 |
| Muestras volcánicas | 1821 |
| Clases volcánicas | 9 |
| Muestras plutónicas | 1066 |
| Clases plutónicas | 10 |

Clases volcánicas:

- andesita
- andesita basáltica
- basalto
- benmoreita
- dacita
- latita
- riodacita
- riolita
- shoshonita

Clases plutónicas:

- diorita
- gabro
- gabrodiorita
- granito
- granodiorita
- monzodiorita
- monzogranito
- monzonita
- sienogranito
- tonalita

La distribución continúa desbalanceada. Andesita es la clase más frecuente, con 901 muestras, mientras gabrodiorita tiene 20. Esta diferencia justifica conservar métricas como MCC y F1 macro además de la exactitud global.

## 4. Curación y control de calidad

La curación consolida nombres litológicos en español, separa el nombre principal de descriptores secundarios y fusiona clases raras con equivalentes petrograficamente compatibles. Entre las reclasificaciones documentadas se encuentran aplita a granito, dolerita a gabro, adamelita a monzogranito, metatonalita a tonalita, traquiandesita a latita y lamprófiro a shoshonita.

Quality_Flag se mantiene como variable de QA/QC y no como predictor. Su función es identificar muestras normales, sospechosas o excluibles. Las muestras con FLAG igual a 2 se excluyen del entrenamiento, mientras que la variable no ingresa a los modelos para evitar mezclar calidad analítica con litología.

## 5. GeoNormPy

GeoNormPy implementa el cálculo de mineralogía normativa CIPW dentro del ecosistema Python. Sus capacidades principales incluyen:

- Normalización anhidra de óxidos.
- Conversión de porcentajes en peso a moles.
- Manejo explícito de FeO, Fe2O3 y FeOT.
- Asignación secuencial de fases normativas.
- Evaluación de saturación en sílice y estado de alúmina.
- Diagnóstico del balance de masa y errores de cálculo.
- Procesamiento individual y por lotes.
- Interfaz de línea de comandos para validación y ejecución.

Los diagnósticos de GeoNormPy sirven para auditoría. No deben incorporarse automáticamente como predictores si representan calidad de cálculo o condiciones derivadas que puedan introducir una ventaja artificial.

## 6. Conjuntos de variables

Los conjuntos declarados actualmente son:

| Conjunto | Variables | Uso |
|---|---:|---|
| oxides_core | 12 | Baseline de óxidos mayores |
| oxides | 17 | Comparación con elementos de baja completitud |
| cipw | 27 | Mineralogía normativa |
| combined_core | 39 | Química mayor más CIPW |
| combined | 44 | Combinación extendida no recomendada |
| oxides_contextual | 14 | Experimento con clases derivadas |
| combined_contextual | 41 | Experimento con clases derivadas |
| combined_enriched | 46 | Química, CIPW e índices petrológicos |
| combined_enriched_spatial | 48 | Modelo espacial oficial |
| combined_enriched_geodata | 53 | Experimental por riesgo de fuga |
| combined_full | 55 | Experimental |

### 6.1 Baseline geoquímico

combined_core integra 12 variables geoquímicas y 27 minerales CIPW.

Óxidos principales:

- SiO2, TiO2, Al2O3, FeOT, CaO, MgO, MnO, K2O, Na2O, P2O5, LOI y Sum_Oxs.

Minerales normativos:

- Q, Cor, Or, Ab, An, Le, Ne, Kp, Ac, Di, Hd, Wo, En, Fs, Fo, Fa, Mt, Hm, Ilm, Ru, Tn, Ap, Cc, Py, Th, ns y ks.

### 6.2 Modelo espacio-contextual

combined_enriched_spatial agrega a combined_core siete índices petrológicos y dos variables espaciales continuas.

Índices petrológicos:

- Porcentaje de anortita en plagioclasa.
- SUM_QAP.
- SUM_CIPW.
- Índice de saturación en alúmina, ASI.
- Número de magnesio, Mg_num.
- Índice de diferenciación de Thornton y Tuttle, DI_Tuttle.
- Índice de color normativo, ICN.

Variables espaciales:

- Trench_Dist, distancia a la fosa en kilómetros.
- LAT, latitud de la muestra.

Trench_Dist puede calcularse directamente a partir de longitud y latitud mediante la implementación vectorizada del proyecto. El flujo de inferencia no necesita archivos SIG pesados para obtener esta variable.

Estas variables son proxies de posición dentro del arco magmático: `Trench_Dist` representa la posición transversal y `LAT` la variación longitudinal. Por ello, `combined_enriched_spatial` se define como un modelo espacio-contextual para el dominio andino/peruano evaluado, no como un clasificador geoquímico universal. Para aplicaciones fuera de ese dominio, o sin coordenadas confiables, la ruta recomendada es el baseline `combined_core`.

## 7. Variables excluidas de producción

No forman parte de los modelos oficiales:

- Quality_Flag, porque representa control de calidad.
- Clase_SiO2 y Serie_Mag, porque resumen fronteras composicionales ya presentes.
- CO2, F, Cl, SO3 y S, por su baja completitud.
- Geol_Unit, Metal_Belt y UTM_Zone, por dependencia regional y riesgo de fuga de información.
- Fault_Dist y Geol_Age_100k no se usan en el flujo oficial actual.

Los pipelines que incorporan geodatos locales permanecen como experimentales. Sus resultados no deben interpretarse como evidencia de generalización fuera del área cartografiada.

## 8. Evaluación reproducible

El benchmark evalúa RandomForest, SVM con PCA y XGBoost mediante validación cruzada estratificada de 5 pliegues. La evaluación se realiza por separado para los dominios volcánico y plutónico.

La partición estratificada mantiene las proporciones de clase, pero no impone separación geográfica entre pliegues. En consecuencia, los resultados de `combined_enriched_spatial` pueden beneficiarse de autocorrelación espacial entre muestras cercanas de entrenamiento y validación. Sus métricas se interpretan como desempeño dentro del dominio muestreado; una demostración de generalización espacial independiente requerirá validación por bloques geográficos o por grupos espaciales.

Las métricas registradas son:

- Exactitud, CA.
- AUC macro uno contra el resto.
- F1 ponderado y F1 macro.
- Precisión y exhaustividad ponderadas y macro.
- Coeficiente de correlación de Matthews, MCC.

La imputación numérica se realiza por mediana. La rama SVM aplica escalamiento y PCA con retención del 95 por ciento de la varianza. RandomForest y XGBoost conservan configuraciones reproducibles con semilla fija.

## 9. Modelos oficiales y resultados

El sistema oficial contiene cuatro modelos:

| Dominio | Ruta de inferencia | Variables | Algoritmo | CA | AUC macro | MCC | F1 ponderado |
|---|---|---|---|---:|---:|---:|---:|
| Volcánicas | Sin coordenadas | combined_core | XGBoost | 0.8056 | 0.9563 | 0.7183 | 0.8032 |
| Plutónicas | Sin coordenadas | combined_core | RandomForest | 0.6154 | 0.8697 | 0.5230 | 0.5861 |
| Volcánicas | Con coordenadas | combined_enriched_spatial | XGBoost | 0.8281 | 0.9640 | 0.7506 | 0.8258 |
| Plutónicas | Con coordenadas | combined_enriched_spatial | XGBoost | 0.6567 | 0.9057 | 0.5776 | 0.6458 |

Los resultados `combined_core` constituyen la referencia principal y transferible del sistema. Los resultados `combined_enriched_spatial` se reportan como mejora contextual regional: no incluyen unidades geológicas, franjas metalogénicas ni otros geodatos locales, pero su interpretación está limitada al dominio espacial evaluado.

### 9.1 Volcánicas

El modelo espacial mejora la exactitud del baseline oficial de 80.56 a 82.81 por ciento y eleva el MCC de 0.7183 a 0.7506. El resultado indica que latitud y distancia a la fosa aportan contexto útil sin sustituir la señal geoquímica y normativa.

Aunque otros pipelines pueden obtener variaciones pequeñas en una métrica particular, XGBoost con combined_core se conserva como baseline geoquímico oficial por su integración de óxidos y CIPW. El modelo espacial se recomienda cuando existen coordenadas válidas dentro de un contexto compatible con los Andes.

### 9.2 Plutónicas

El baseline oficial usa RandomForest con combined_core y obtiene 61.54 por ciento de exactitud. RandomForest con oxides_core alcanza 62.20 por ciento, una diferencia de 0.66 puntos porcentuales. Se mantiene combined_core como decisión metodológica porque incorpora mineralogía normativa y conserva coherencia con la interpretación QAPF.

El modelo espacial plutónico mejora la exactitud hasta 65.67 por ciento y el MCC hasta 0.5776. Aun así, este dominio sigue siendo más difícil porque varias clases plutónicas forman continuidades composicionales cuya separación tradicional depende también de moda mineral, textura y contexto geológico.

## 10. Interpretación geológica

Las rocas volcánicas presentan mayor separabilidad porque muchas clases siguen gradientes amplios de sílice, álcalis y mineralogía normativa. El dominio plutónico contiene transiciones más continuas entre granito, granodiorita, tonalita, monzonita, monzodiorita, diorita, gabro y clases relacionadas.

La mejora espacial es plausible en un arco magmático segmentado: la distancia a la fosa representa posición transversal al arco y la latitud captura variación longitudinal. Sin embargo, el modelo espacial debe entenderse como contextual para los Andes peruanos evaluados y no como universal. Para muestras sin coordenadas, fuera del dominio espacial de entrenamiento o de otros países, debe utilizarse el baseline geoquímico. La validación estratificada actual no reemplaza una validación por bloques geográficos, necesaria para cuantificar generalización espacial independiente.

### 10.1 Componente TAS para contraste químico, CIPW y litología reportada

Se incorporó un componente TAS (SiO₂ frente a Na₂O + K₂O) con los óxidos mayores normalizados a 100 por ciento anhidro. En las rocas volcánicas, TAS se usa como referencia de clasificación química y permite contrastar la posición composicional de cada muestra con su litología reportada y con el estado de saturación en sílice calculado por CIPW. La comparación no pretende que los tres criterios sean equivalentes: TAS clasifica desde química de roca total, mientras CIPW obtiene una mineralogía normativa a partir de esa química.

Las figuras `artifacts/tas_comparison/tas_cipw_litologia_vol.png` y `artifacts/tas_comparison/concordancia_litologia_cipw_vol.png` presentan respectivamente la distribución TAS por litología reportada, la saturación normativa CIPW y la proporción de clases sobresaturadas o subsaturadas. Esto hace visibles coincidencias composicionales y casos que requieren revisión petrológica, sin reinterpretar automáticamente el target del dataset.

Como contraste cuantitativo adicional, `artifacts/tas_comparison/concordancia_tas_litologia_vol.png` muestra la distribución de `ROCK_NAME` dentro de cada campo TAS volcánico comparable, y `resumen_concordancia_tas_litologia_vol.csv` entrega los conteos y proporciones compatibles. La matriz no presenta esta relación como una validación modal: `ROCK_NAME` es litología reportada. Se excluyen de esa tabla los campos TAS sin equivalencia directa en las categorías del dataset para no forzar una correspondencia petrológica; en la versión actual, 640 de 1,806 muestras volcánicas (35.4 %) quedan en campos comparables.

Para las plutónicas, el mismo espacio SiO₂–álcalis se conserva solamente como referencia composicional. No se utiliza como clasificación formal ni para validar nombres plutónicos: la referencia petrográfica apropiada es QAPF cuando se dispone de mineralogía modal. `ROCK_NAME` es la litología reportada y normalizada del dataset; no representa una nueva medición modal. Las figuras plutónicas se rotulan explícitamente con esta limitación.

Este componente se mantiene fuera de los conjuntos de variables oficiales y no alimenta los modelos de ML. Su finalidad es aportar trazabilidad e interpretación, no introducir una variable derivada que pueda simplificar artificialmente el problema. La clasificación TAS de referencia sigue a Le Bas, Le Maitre, Streckeisen y Zanettin (1986), DOI: 10.1093/petrology/27.3.745.

## 11. Interpretabilidad

El repositorio contiene resultados SHAP para los modelos espaciales oficiales:

- artifacts/shap_interpretation/volcanic_shap_bar.png
- artifacts/shap_interpretation/volcanic_shap_detail_riolita.png
- artifacts/shap_interpretation/plutonic_shap_bar.png
- artifacts/shap_interpretation/plutonic_shap_detail_granito.png

Estos artefactos permiten revisar la contribución global de variables y casos de detalle para riolita y granito. Su interpretación debe acompañarse de control geológico para distinguir asociaciones plausibles de patrones específicos del dataset.

## 12. Exportación y transferencia a PetroPyQAPF

Los modelos oficiales se encuentran en artifacts/official_models y se replican en artifacts/petropyqapf_transfer/models.

| Dominio | Tipo | Archivo |
|---|---|---|
| Volcánicas | Baseline | volcanic__combined_core__XGBoost.joblib |
| Plutónicas | Baseline | plutonic__combined_core__RandomForest.joblib |
| Volcánicas | Espacial | volcanic__combined_enriched_spatial__XGBoost.joblib |
| Plutónicas | Espacial | plutonic__combined_enriched_spatial__XGBoost.joblib |

El paquete de transferencia incluye:

- Cuatro modelos oficiales.
- Manifiesto CSV y resumen JSON.
- Esquema del bundle oficial.
- Catálogo ampliado de modelos secundarios y experimentales.
- Especificación de integración.
- Predictor de referencia.
- Reglas de enrutamiento y advertencias metodológicas.

El enrutamiento previsto es:

1. Confirmar el dominio VOL o PLU.
2. Si faltan coordenadas, usar el baseline combined_core.
3. Si existen longitud y latitud válidas, calcular Trench_Dist.
4. Usar el modelo combined_enriched_spatial correspondiente.
5. Entregar clase predicha, probabilidades y advertencias aplicables.

La predicción debe considerarse apoyo computacional y no reemplazo de la determinación petrográfica.

## 13. Estado de los entregables

| Entregable | Estado |
|---|---|
| Dataset oficial v5 espacial | Disponible |
| Motor CIPW GeoNormPy | Implementado |
| Feature sets declarados | Implementados |
| Benchmark de 5 pliegues | Ejecutado |
| Matrices de confusión y curvas ROC | Disponibles |
| Análisis SHAP de modelos espaciales | Disponible |
| Cuatro modelos oficiales | Exportados |
| Paquete de transferencia | Preparado |
| Integración ejecutada en PetroPyQAPF | No confirmada en este repositorio |
| Validación externa independiente | Pendiente |

## 14. Limitaciones

- No existe todavía validación externa independiente con otro dataset regional.
- El desbalance entre clases afecta especialmente a las clases minoritarias.
- El dominio plutónico conserva ambigüedades que la geoquímica de roca total no resuelve por completo.
- Los modelos espaciales son contextuales y requieren cautela fuera de los Andes peruanos.
- GeoNormPy aún necesita una comparación sistemática documentada contra motores normativos externos.
- La existencia del paquete de transferencia no demuestra por sí sola que la integración final en PetroPyQAPF haya sido validada en ejecución.

## 15. Trabajo pendiente prioritario

1. Validar los modelos con un conjunto externo no usado en la curación ni el entrenamiento.
2. Revisar errores y métricas por clase, con atención especial a las clases minoritarias.
3. Comparar GeoNormPy contra un conjunto normativo de referencia.
4. Validar dentro de PetroPyQAPF el enrutamiento, las columnas requeridas, las probabilidades y los mensajes de advertencia.
5. Documentar el dominio espacial recomendado y el comportamiento fuera de él.
6. Preparar una versión académica abreviada con metodología, resultados, discusión y limitaciones.

## 16. Relación con el abstract aceptado en el XXIII CPG 2026

El documento GEONORM_Abstract.docx representa una etapa anterior y válida del proyecto, basada en el dataset v4 de 2755 muestras. En esa versión se seleccionaron dos modelos: XGBoost con combined_core para 1764 muestras volcánicas y RandomForest con oxides_core para 991 muestras plutónicas. Sus resultados fueron CA de 0.8049 y MCC de 0.7131 para volcánicas, y CA de 0.5812 y MCC de 0.4815 para plutónicas.

El estado actual no invalida esos resultados. Corresponde a una ampliación posterior del trabajo:

- El dataset aumentó de 2755 a 2887 muestras.
- El dominio volcánico aumentó de 1764 a 1821 muestras.
- El dominio plutónico aumentó de 991 a 1066 muestras.
- El baseline plutónico oficial cambió de oxides_core a combined_core por coherencia petrológica y normativa.
- Se incorporaron modelos espacio-contextuales con latitud y distancia a la fosa.
- Se generaron resultados SHAP y un paquete ampliado de transferencia a PetroPyQAPF.

Para el póster y el trabajo técnico completo del Congreso deben utilizarse los resultados actuales, manteniendo el título y la autoría aprobados. La actualización debe presentarse de forma transparente mediante una nota metodológica como la siguiente:

Después de la aceptación del resumen, el dataset fue ampliado de 2755 a 2887 muestras y se incorporó una ruta espacio-contextual. Los resultados originales se conservan como baseline de la versión v4, mientras que las métricas aquí presentadas corresponden al pipeline actualizado sobre el dataset v5.

Los resultados espaciales no deben mostrarse como una corrección retroactiva del experimento anterior ni como si provinieran del mismo conjunto de variables. Son una nueva ruta de inferencia, aplicable cuando existen coordenadas válidas. Para conservar la trazabilidad, toda tabla o figura debe identificar la versión del dataset, el conjunto de variables, el algoritmo y el tipo de validación.

## 17. Conclusiones

GeoNormML y GeoNormPy constituyen actualmente una arquitectura reproducible para clasificación litogeoquímica de rocas ígneas. El dataset oficial contiene 2887 muestras y 19 clases, el benchmark separa los dominios volcánico y plutónico, y los artefactos productivos cubren tanto entradas sin coordenadas como entradas con contexto espacial.

La mejor ruta disponible utiliza XGBoost con combined_enriched_spatial y alcanza 82.81 por ciento de exactitud en volcánicas y 65.67 por ciento en plutónicas. Cuando no existen coordenadas, los baselines oficiales son XGBoost con combined_core para volcánicas y RandomForest con combined_core para plutónicas.

La principal fortaleza metodológica es la separación entre variables transferibles y variables con riesgo de fuga. La inclusión de latitud y distancia a la fosa aporta contexto geológico continuo, mientras que unidad geológica, cinturón metalogenético y zona UTM quedan fuera de producción.

El proyecto está preparado para transferencia técnica, pero todavía no puede considerarse validado de extremo a extremo hasta ejecutar la integración en PetroPyQAPF y completar una validación externa independiente.

## 18. Título sugerido para publicación

GeoNormML y GeoNormPy: integración reproducible de norma CIPW, contexto tectónico y aprendizaje supervisado para la clasificación de rocas ígneas del Perú
