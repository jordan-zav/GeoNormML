# GeoNormPy y GeoNormML: ecosistema reproducible en Python para el cálculo normativo CIPW y la clasificación supervisada de rocas ígneas del Perú

Jordan Zavaleta1

1 Escuela Profesional de Ingeniería Geológica, Universidad Nacional de Ingeniería, Lima, Perú

## 1. Resumen

Este trabajo presenta GeoNormPy y GeoNormML, un ecosistema reproducible en Python para integrar el cálculo normativo CIPW, la curación litogeoquímica y la clasificación supervisada de rocas ígneas del Perú. GeoNormPy implementa un motor propio para el cálculo de minerales normativos a partir de óxidos mayores, con manejo explícito de hierro, normalización anhidra, control de saturación en sílice y trazabilidad diagnóstica. GeoNormML organiza el flujo de preparación del dataset, definición de variables, entrenamiento, validación cruzada, selección de modelos y exportación de artefactos para transferencia. El conjunto final comprende 2755 muestras, 19 clases litológicas y dos dominios operativos: rocas volcánicas, con 1764 muestras y 9 clases, y rocas plutónicas, con 991 muestras y 10 clases. Se evaluaron Random Forest, XGBoost y SVM con PCA mediante validación cruzada estratificada de cinco pliegues. El modelo seleccionado para rocas volcánicas fue XGBoost con variables combinadas de óxidos mayores y minerales normativos, alcanzando CA de 0.804989, AUC macro de 0.947036, F1 ponderado de 0.802379 y MCC de 0.713056. Para rocas plutónicas, el modelo seleccionado fue Random Forest con óxidos mayores principales, alcanzando CA de 0.581231, AUC macro de 0.852232, F1 ponderado de 0.539664 y MCC de 0.481521. Los resultados muestran que la integración entre geoquímica de roca total, mineralogía normativa y aprendizaje automático permite construir un sistema trazable de apoyo a la denominación litológica, con mayor separabilidad en rocas volcánicas y mayor complejidad composicional en rocas plutónicas.

Palabras clave: GeoNormPy, GeoNormML, CIPW, aprendizaje automático, rocas ígneas, litogeoquímica, Perú.

## 2. Abstract

This work presents GeoNormPy and GeoNormML, a reproducible Python ecosystem for integrating CIPW normative calculation, lithogeochemical data curation, and supervised classification of igneous rocks from Peru. GeoNormPy implements a local engine for deriving normative minerals from major oxides, with explicit iron handling, anhydrous normalization, silica saturation control, and diagnostic traceability. GeoNormML structures the workflow for dataset preparation, feature definition, model training, cross-validation, model selection, and artifact export. The final dataset includes 2755 samples, 19 lithological classes, and two operational domains: volcanic rocks, with 1764 samples and 9 classes, and plutonic rocks, with 991 samples and 10 classes. Random Forest, XGBoost, and SVM with PCA were evaluated using five-fold stratified cross-validation. The selected volcanic model was XGBoost using a combined set of major oxides and normative minerals, reaching CA of 0.804989, macro AUC of 0.947036, weighted F1 of 0.802379, and MCC of 0.713056. The selected plutonic model was Random Forest using core major oxides, reaching CA of 0.581231, macro AUC of 0.852232, weighted F1 of 0.539664, and MCC of 0.481521. The results show that total-rock geochemistry, normative mineralogy, and machine learning can form a traceable system for lithological naming support, with stronger separability in volcanic rocks and higher compositional overlap in plutonic rocks.

Keywords: GeoNormPy, GeoNormML, CIPW, machine learning, igneous rocks, lithogeochemistry, Peru.

## 3. Introducción

La denominación de rocas ígneas integra observación petrográfica, relaciones de campo, geoquímica de roca total y criterios mineralógicos. En este marco, la norma CIPW constituye una herramienta clásica para transformar composiciones expresadas en óxidos mayores en una mineralogía normativa idealizada. Aunque esta mineralogía no reemplaza a la moda real, permite comparar composiciones, reconocer estados de saturación en sílice y resumir tendencias químicas relevantes para la clasificación.

El desarrollo de herramientas computacionales abiertas permite convertir este procedimiento en un flujo reproducible, auditable y transferible. GeoNormPy y GeoNormML fueron diseñados con ese propósito. El primero resuelve el cálculo normativo CIPW dentro del ecosistema Python, mientras que el segundo integra datos depurados, variables geoquímicas y normativas, validación de modelos y exportación de clasificadores. La contribución central no es solo la aplicación de algoritmos supervisados, sino la construcción de una arquitectura metodológica capaz de separar control de calidad, variables predictivas, descriptores derivados y criterios de selección de modelos.

El objetivo de este trabajo es presentar la estructura del ecosistema GeoNormPy-GeoNormML, documentar el dataset final de rocas ígneas del Perú, evaluar modelos supervisados por dominio litológico y discutir la coherencia petrológica de los resultados obtenidos. El enfoque diferencia explícitamente rocas volcánicas y plutónicas, debido a que ambos grupos responden a criterios de clasificación y grados de separabilidad geoquímica distintos.

## 4. Materiales y métodos

### 4.1. Dataset litogeoquímico

El dataset final contiene 2755 muestras de rocas ígneas del Perú, organizadas en 19 clases litológicas finales. Las muestras fueron separadas en dos dominios: volcánico y plutónico. El dominio volcánico incluye 1764 muestras distribuidas en 9 clases: andesita, andesita basáltica, basalto, benmoreita, dacita, latita, riodacita, riolita y shoshonita. El dominio plutónico incluye 991 muestras distribuidas en 10 clases: diorita, gabro, gabrodiorita, granito, granodiorita, monzodiorita, monzogranito, monzonita, sienogranito y tonalita.

La curación litológica buscó mantener clases con significado petrológico y soporte estadístico suficiente. Los nombres fueron estandarizados en español y se consolidaron etiquetas raras, texturales o composicionalmente equivalentes dentro de clases principales. El objetivo fue evitar que el modelo aprendiera fragmentos terminológicos sin estabilidad estadística o sin correspondencia clara con el problema geoquímico.

El control de calidad geoquímica se mantuvo separado del entrenamiento. Las variables de QA/QC se utilizaron para filtrar y auditar muestras, pero no como predictores litológicos. Esta separación evita mezclar señales de confiabilidad analítica con señales de composición o mineralogía.

### 4.2. GeoNormPy

GeoNormPy es un motor local para el cálculo de la norma CIPW. El procedimiento incluye normalización anhidra, conversión de porcentajes en peso a moles, distribución secuencial de fases accesorias, feldespatos, silicatos máficos y fases de saturación en sílice. El algoritmo considera distintos escenarios de hierro: FeO y Fe2O3 medidos, FeOT como hierro total, y casos incompletos o inconsistentes.

Además de minerales normativos, GeoNormPy entrega diagnósticos interpretativos como estado de saturación en sílice, estado de alúmina, modo de hierro, advertencias de hierro y balance de masa. Estas salidas son relevantes para auditoría y trazabilidad, aunque no todas se usan como predictores oficiales.

### 4.3. GeoNormML

GeoNormML organiza el pipeline de machine learning. El flujo comprende carga del dataset, separación por dominio litológico, definición de conjuntos de variables, preprocesamiento, entrenamiento, validación cruzada, cálculo de métricas, generación de matrices de confusión, curvas ROC y exportación de modelos finales.

Se definieron tres familias principales de variables:

| Conjunto | Contenido | Estado |
|---|---|---|
| oxides_core | Óxidos mayores principales, LOI y suma de óxidos | Oficial |
| cipw | Minerales normativos calculados por GeoNormPy | Oficial |
| combined_core | oxides_core más cipw | Oficial |

También se evaluaron conjuntos secundarios o experimentales que incluyen variables de baja completitud o descriptores derivados. Estas variables se conservaron para análisis comparativo, pero no se adoptaron como baseline oficial cuando su ganancia fue marginal o cuando podían codificar indirectamente fronteras ya presentes en la química de óxidos.

### 4.4. Modelos y validación

Se evaluaron tres algoritmos supervisados:

- Random Forest.
- XGBoost.
- SVM con PCA.

La evaluación se realizó mediante validación cruzada estratificada de cinco pliegues, separando los dominios volcánico y plutónico. Las métricas calculadas fueron CA, AUC macro one-vs-rest, F1 ponderado, precisión ponderada, recall ponderado, MCC, F1 macro, precisión macro y recall macro. La selección final no se basó únicamente en el máximo valor aislado de CA, sino en el equilibrio entre desempeño, estabilidad, interpretabilidad, disponibilidad de variables y coherencia petrológica.

## 5. Resultados

### 5.1. Modelos seleccionados

Los modelos seleccionados para uso oficial fueron:

| Dominio | Feature set | Modelo | Muestras | Clases | CA | AUC macro | F1 ponderado | MCC |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Volcánico | combined_core | XGBoost | 1764 | 9 | 0.804989 | 0.947036 | 0.802379 | 0.713056 |
| Plutónico | oxides_core | Random Forest | 991 | 10 | 0.581231 | 0.852232 | 0.539664 | 0.481521 |

En rocas volcánicas, el modelo XGBoost con variables combinadas de óxidos mayores y minerales normativos presentó el mejor equilibrio dentro de los conjuntos oficiales. Su desempeño indica que la combinación entre composición mayor y mineralogía normativa captura adecuadamente la estructura geoquímica de las clases volcánicas.

En rocas plutónicas, el mejor modelo oficial fue Random Forest con óxidos mayores principales. La incorporación de variables normativas no superó de forma consistente al conjunto de óxidos principales, lo cual sugiere que las fronteras entre litologías plutónicas del dataset se relacionan de manera compleja con la química total y que la información modal real sigue siendo crítica para una separación más robusta.

### 5.2. Comparación de modelos en rocas volcánicas

| Feature set | Modelo | CA | AUC macro | F1 ponderado | MCC |
|---|---|---:|---:|---:|---:|
| oxides_core | Random Forest | 0.806122 | 0.946580 | 0.799935 | 0.711057 |
| oxides_core | XGBoost | 0.797052 | 0.947686 | 0.793605 | 0.700497 |
| oxides_core | SVM con PCA | 0.658163 | 0.934046 | 0.672215 | 0.572915 |
| cipw | Random Forest | 0.784580 | 0.937844 | 0.777537 | 0.677949 |
| cipw | XGBoost | 0.780612 | 0.937420 | 0.775796 | 0.674713 |
| cipw | SVM con PCA | 0.625850 | 0.917156 | 0.646361 | 0.536375 |
| combined_core | Random Forest | 0.798753 | 0.950337 | 0.792503 | 0.699929 |
| combined_core | XGBoost | 0.804989 | 0.947036 | 0.802379 | 0.713056 |
| combined_core | SVM con PCA | 0.670068 | 0.932696 | 0.681999 | 0.587468 |

Los algoritmos basados en árboles dominaron el rendimiento volcánico. La diferencia entre Random Forest y XGBoost fue pequeña, pero XGBoost con combined_core alcanzó el MCC más alto entre los modelos oficiales y fue seleccionado como modelo volcánico principal.

### 5.3. Comparación de modelos en rocas plutónicas

| Feature set | Modelo | CA | AUC macro | F1 ponderado | MCC |
|---|---|---:|---:|---:|---:|
| oxides_core | Random Forest | 0.581231 | 0.852232 | 0.539664 | 0.481521 |
| oxides_core | XGBoost | 0.545913 | 0.840428 | 0.519882 | 0.439805 |
| oxides_core | SVM con PCA | 0.418769 | 0.832914 | 0.435801 | 0.334374 |
| cipw | Random Forest | 0.536831 | 0.841420 | 0.507264 | 0.427241 |
| cipw | XGBoost | 0.517659 | 0.818801 | 0.495701 | 0.405236 |
| cipw | SVM con PCA | 0.389506 | 0.827207 | 0.413287 | 0.304406 |
| combined_core | Random Forest | 0.568113 | 0.856596 | 0.531131 | 0.465411 |
| combined_core | XGBoost | 0.534813 | 0.841911 | 0.513013 | 0.427178 |
| combined_core | SVM con PCA | 0.431887 | 0.840223 | 0.453890 | 0.348225 |

El desempeño plutónico fue menor que el volcánico, pero consistente con la naturaleza del problema. Las rocas plutónicas presentan campos composicionales superpuestos y muchas de sus distinciones dependen de proporciones modales reales. En este dominio, Random Forest con oxides_core fue el modelo más sólido dentro de los criterios oficiales.

### 5.4. Matrices de confusión

Las matrices de confusión generadas para este trabajo se encuentran en:

artifacts/report_confusion_matrices_2025_context

Figuras sugeridas para inserción:

- Figura 1. Matriz de confusión para rocas volcánicas usando XGBoost con combined_core.
- Figura 2. Matriz de confusión para rocas plutónicas usando Random Forest con oxides_core.
- Figura 3. Comparación de matrices volcánicas entre Random Forest, XGBoost y SVM con PCA.
- Figura 4. Comparación de matrices plutónicas entre Random Forest, XGBoost y SVM con PCA.

En rocas volcánicas, los mayores aciertos se concentran en clases con campos geoquímicos amplios y bien representados, especialmente andesita, dacita y riolita. Las confusiones principales se producen entre clases composicionalmente cercanas, como basalto, andesita basáltica y andesita, o entre dacita, riodacita y riolita.

En rocas plutónicas, los errores se concentran en gradientes petrogenéticamente esperables: granito, monzogranito, granodiorita y tonalita, así como gabro, gabrodiorita y diorita. Este patrón es coherente con la continuidad composicional de los campos QAPF y con la ausencia de información modal directa.

## 6. Discusión

La diferencia de rendimiento entre rocas volcánicas y plutónicas refleja una diferencia geológica real. En rocas volcánicas, las clases suelen responder mejor a gradientes de sílice, álcalis, saturación normativa y evolución magmática. Por ello, la combinación de óxidos mayores y minerales normativos permite capturar patrones suficientemente definidos para el aprendizaje supervisado.

En rocas plutónicas, la clasificación depende de proporciones modales que no siempre se expresan de forma única en la química total. Rocas como granito, granodiorita, tonalita y monzogranito pueden ocupar espacios composicionales cercanos, especialmente cuando se trabaja con datasets regionales y con nombres provenientes de fuentes heterogéneas. El resultado obtenido no debe interpretarse como una debilidad aislada del algoritmo, sino como una limitación inherente al uso de química de roca total para aproximar un sistema de clasificación originalmente modal.

El uso de GeoNormPy permite que la mineralogía normativa sea calculada dentro del mismo entorno reproducible del modelamiento. Esto fortalece la trazabilidad entre óxidos de entrada, minerales normativos y variables usadas por los modelos. Sin embargo, los resultados también muestran que no toda variable derivada debe incorporarse automáticamente. Un modelo útil para interpretación petrológica debe priorizar señales disponibles, auditables y geológicamente justificables.

La selección de modelos adopta por ello un criterio conservador. En rocas volcánicas, combined_core con XGBoost representa el mejor balance entre desempeño y riqueza petrológica de variables. En rocas plutónicas, oxides_core con Random Forest evita introducir complejidad normativa que no mejora consistentemente el desempeño. Esta diferencia por dominio es metodológicamente relevante: el ecosistema no fuerza una única arquitectura para todos los tipos de rocas, sino que selecciona el flujo más defendible para cada caso.

## 7. Conclusiones

GeoNormPy y GeoNormML conforman un ecosistema reproducible para integrar cálculo normativo CIPW, curación litogeoquímica y clasificación supervisada de rocas ígneas.

El dataset final contiene 2755 muestras y 19 clases litológicas, separadas en dominios volcánico y plutónico. Esta separación mejora la coherencia del problema de clasificación y respeta diferencias petrológicas fundamentales entre ambos grupos.

El modelo oficial para rocas volcánicas fue XGBoost con combined_core, alcanzando CA de 0.804989, AUC macro de 0.947036, F1 ponderado de 0.802379 y MCC de 0.713056.

El modelo oficial para rocas plutónicas fue Random Forest con oxides_core, alcanzando CA de 0.581231, AUC macro de 0.852232, F1 ponderado de 0.539664 y MCC de 0.481521.

Las rocas volcánicas muestran mayor separabilidad geoquímica que las plutónicas, mientras que las plutónicas evidencian confusiones coherentes con la superposición de campos composicionales y la dependencia de información modal.

La combinación entre geoquímica, norma CIPW y aprendizaje automático funciona como una herramienta de apoyo a la interpretación petrológica, no como reemplazo del criterio geológico. Su valor principal reside en la trazabilidad, reproducibilidad y capacidad de reconocer patrones multiclase en datasets regionales.

## 8. Trabajo futuro

Las etapas siguientes deben enfocarse en validar los modelos con datasets externos, comparar GeoNormPy contra otros motores normativos, incorporar análisis de importancia de variables y explorar descriptores modales o texturales cuando estén disponibles. También se recomienda integrar los modelos oficiales en herramientas de clasificación petrológica digital, manteniendo probabilidades, advertencias y trazabilidad de variables como parte de la salida interpretativa.

## 9. Referencias

Breiman, L. 2001. Random forests. Machine Learning, 45, 5-32.

Caté, A., Schetselaar, E., Mercier-Langevin, P. y Ross, P.-S. 2018. Classification of lithostratigraphic and alteration units from drillhole lithogeochemical data using machine learning: a case study from the Lalor volcanogenic massive sulphide deposit, Snow Lake, Manitoba, Canada. Journal of Geochemical Exploration, 188, 216-228.

Chen, T. y Guestrin, C. 2016. XGBoost: A scalable tree boosting system. Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, 785-794.

Cortes, C. y Vapnik, V. 1995. Support-vector networks. Machine Learning, 20, 273-297.

Cross, W., Iddings, J. P., Pirsson, L. V. y Washington, H. S. 1902. A quantitative chemico-mineralogical classification and nomenclature of igneous rocks. Journal of Geology, 10, 555-690.

González-Guzmán, R., Elizondo-Pacheco, L. A., González-Roque, A., Sánchez-Torres, C. E. y Cárdenas-Muñoz, K. S. 2023. shinyNORRRM: A cross-platform software to calculate the CIPW norm. Mathematical Geosciences, 55, 563-577.

Le Bas, M. J., Le Maitre, R. W., Streckeisen, A. y Zanettin, B. 1986. A chemical classification of volcanic rocks based on the total alkali-silica diagram. Journal of Petrology, 27, 745-750.

Le Maitre, R. W. et al. 2002. Igneous Rocks: A Classification and Glossary of Terms. Cambridge University Press.

Middlemost, E. A. K. 1989. Iron oxidation ratios, norms and the classification of volcanic rocks. Chemical Geology, 77, 19-26.

Nathwani, C. L., Wilkinson, J. J., Fry, G., Armstrong, R. N., Smith, D. J. e Ihlenfeld, C. 2022. Machine learning for geochemical exploration: classifying metallogenic fertility in arc magmas and insights into porphyry copper deposit formation. Mineralium Deposita, 57, 1143-1166.

Petrelli, M. 2024. Machine learning in petrology: state-of-the-art and future perspectives. Journal of Petrology, 65, egae036.

Rollinson, H. 1993. Using Geochemical Data: Evaluation, Presentation, Interpretation. Longman.

Streckeisen, A. 1976. To each plutonic rock its proper name. Earth-Science Reviews, 12, 1-33.

Winter, J. D. 2010. Principles of Igneous and Metamorphic Petrology. Pearson Prentice Hall.
