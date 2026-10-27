# Sistematización Metodológica del Dataset y de la Ingeniería de Variables en GeoNormML

## 1. Introducción

El desarrollo de modelos supervisados para la clasificación litológica de rocas ígneas exige no solo un conjunto de datos confiable, sino también una trazabilidad rigurosa de cada etapa de transformación aplicada a dicho conjunto. En el caso del proyecto precursor de `GeoNormML`, la lógica metodológica utilizada para construir el dataset final fue consistente desde el punto de vista geoquímico y petrológico, pero quedó distribuida entre distintas fuentes operativas, incluyendo hojas de cálculo, cálculos normativos externos, criterios manuales de curación y notas complementarias no incorporadas de forma explícita en el informe principal.

Esta situación no invalida el trabajo previo; por el contrario, evidencia un proceso de curación e interpretación técnica considerable. Sin embargo, para efectos de reproducibilidad científica, evaluación rigurosa y futura escalabilidad del proyecto, resulta necesario formalizar esa lógica en un marco metodológico claro. El presente documento tiene como objetivo sistematizar la estructura real del dataset, distinguir el origen de sus variables y establecer una base conceptual para su futura reconstrucción íntegra en Python.

## 2. Identificación de las versiones del dataset

En la carpeta [`Dataset`](/I:/GDrive/Projects/In%20Development/GeoNormML/Dataset) se identificaron dos archivos principales que representan diferentes etapas del flujo de trabajo:

### 2.1. Dataset base depurado

Archivo: [`0. Final_Dataset.xlsx`](/I:/GDrive/Projects/In%20Development/GeoNormML/Dataset/0.%20Final_Dataset.xlsx)

Esta versión contiene `2707` muestras y `28` columnas. Su estructura muestra que ya había pasado por un proceso de curación y depuración previo, pues presenta un conjunto estable de identificadores, metadatos, etiquetas litológicas y óxidos mayores. No obstante, todavía no incorpora los minerales normativos CIPW ni diversas variables derivadas calculadas en fases posteriores.

Desde una perspectiva metodológica, esta base debe interpretarse como un dataset intermedio depurado y consolidado, apto para ser enriquecido mediante nuevas transformaciones reproducibles. No corresponde al dataset completamente crudo de origen, pero sí constituye el punto de partida más adecuado para reconstruir el pipeline analítico.

### 2.2. Dataset enriquecido con minerales normativos CIPW y variables derivadas

Archivo: [`0. Final_Dataset+CIPW.xlsx`](/I:/GDrive/Projects/In%20Development/GeoNormML/Dataset/0.%20Final_Dataset%2BCIPW.xlsx)

Esta versión contiene igualmente `2707` muestras, pero expande su estructura a `62` columnas. En ella se incorporan minerales normativos CIPW, variables derivadas a partir de óxidos mayores, indicadores petroquímicos y otros descriptores adicionales empleados durante el modelamiento.

La comparación entre ambas versiones permite afirmar que el archivo enriquecido no representa solo la adición de columnas nuevas, sino una etapa posterior del flujo metodológico en la cual también se realizaron ajustes sobre algunas columnas compartidas. En consecuencia, esta base debe entenderse como un dataset curado y transformado de forma adicional, cercano al insumo definitivo usado en los algoritmos de clasificación.

## 3. Reconstrucción conceptual del flujo de trabajo

El análisis de ambos archivos y del documento auxiliar [`Considerations.docx`](/I:/GDrive/Projects/In%20Development/GeoNormML/Dataset/Considerations.docx) permite reconstruir la arquitectura real del dataset en cinco niveles sucesivos.

### 3.1. Primer nivel: dataset base curado

Este nivel reúne las variables originales o conservadas tras la depuración inicial. Incluye:

- identificadores de muestra;
- fuente de procedencia;
- coordenadas;
- etiquetas litológicas principales y secundarias;
- metadatos texturales y contextuales;
- óxidos mayores;
- pérdida por ignición (`LOI`).

En términos operativos, esta capa representa la base mínima sobre la cual pueden construirse todas las etapas posteriores del pipeline.

### 3.2. Segundo nivel: dataset con variables derivadas geoquímicas

En una segunda etapa se añadieron variables calculadas directamente a partir de los óxidos mayores u otras columnas originales. Entre ellas destacan:

- `Sum_Oxs`
- `Clase_SiO2`
- `Alc`
- `Serie_Mag`
- `Quality_Flag`

Estas variables no pertenecen al contenido original del dataset base y deben considerarse parte de una fase explícita de ingeniería de variables geoquímicas.

### 3.3. Tercer nivel: dataset con cálculo normativo CIPW

Sobre la base de los óxidos mayores se generó un conjunto de minerales normativos mediante el método CIPW. Esta etapa constituye uno de los ejes centrales del proyecto, ya que transforma la composición química en una representación mineralógica teórica con alto valor interpretativo para la clasificación petrológica.

Entre las variables de esta etapa se encuentran:

- `Q`
- `Cor`
- `Ort`
- `Ab`
- `An`
- `Ne`
- `Le`
- `Kp`
- `Hy`
- `Di`
- `Wo`
- `Ol`
- `La`
- `Ac`
- `Na_ms`
- `Mag`
- `Hem`
- `Ilm`
- `Tit`
- `Ru`
- `Pwk`
- `Ap`
- `Cc`
- `Ft`
- `Py`

### 3.4. Cuarto nivel: variables derivadas a partir del cálculo CIPW

Posteriormente se calcularon descriptores adicionales a partir de los minerales normativos. Estas variables resumen relaciones internas entre fases minerales y fueron utilizadas como apoyo en la caracterización petroquímica y el modelamiento. Entre ellas se identifican:

- `%An en Pl`
- `SUM_QAP`
- `SUM_CIPW`
- `ITT`

### 3.5. Quinto nivel: dataset final para modelamiento

El insumo final para los algoritmos de machine learning estuvo constituido por la combinación de:

- variables originales;
- variables derivadas geoquímicas;
- minerales normativos CIPW;
- variables derivadas a partir de CIPW;
- etiquetas litológicas finales.

Por tanto, el dataset usado en el modelamiento no fue únicamente un conjunto de óxidos mayores, sino una matriz de atributos enriquecida mediante razonamiento geoquímico, curación litológica y cálculo normativo.

## 4. Clasificación de las variables por origen metodológico

Para fines de trazabilidad, las columnas pueden ordenarse en cuatro grupos principales.

### 4.1. Variables originales

Pertenecen al dataset base:

- `Final_ID`
- `ID2`
- `ID1`
- `Source`
- `Lab_ID`
- `Long`
- `Lat`
- `Rock_Type`
- `Rock_Name`
- `Sec_Rock_Name`
- `Texture`
- `Sec_Texture`
- `Min`
- `Context`
- `Geo_Age`
- `Sec_Geo_Age`
- `SiO2`
- `TiO2`
- `Al2O3`
- `Fe2O3`
- `FeO`
- `MgO`
- `MnO`
- `CaO`
- `Na2O`
- `K2O`
- `P2O5`
- `LOI`

### 4.2. Variables derivadas geoquímicas

- `Sum_Oxs`
- `Clase_SiO2`
- `Alc`
- `Serie_Mag`
- `Quality_Flag`

### 4.3. Variables normativas CIPW

- `Q`
- `Cor`
- `Ort`
- `Ab`
- `An`
- `Ne`
- `Le`
- `Kp`
- `Hy`
- `Di`
- `Wo`
- `Ol`
- `La`
- `Ac`
- `Na_ms`
- `Mag`
- `Hem`
- `Ilm`
- `Tit`
- `Ru`
- `Pwk`
- `Ap`
- `Cc`
- `Ft`
- `Py`

### 4.4. Variables derivadas de CIPW

- `%An en Pl`
- `ITT`
- `SUM_QAP`
- `SUM_CIPW`

## 5. Reglas y fórmulas ya identificadas

La revisión del Excel procesado y del documento auxiliar permitió recuperar varias reglas concretas que pueden trasladarse directamente a Python.

### 5.1. Clasificación por contenido de sílice

La variable `Clase_SiO2` fue calculada con base en `SiO2` y responde al siguiente esquema:

- `SiO2 >= 63`: `Ácida`
- `52 <= SiO2 < 63`: `Intermedia`
- `45 <= SiO2 < 52`: `Básica`
- `SiO2 < 45`: `Ultramáfica`

### 5.2. Alcalinidad total

La variable `Alc` responde a la expresión:

`Alc = Na2O + K2O`

### 5.3. Serie magmática

La variable `Serie_Mag` sigue una lógica petroquímica basada en álcalis, sílice y minerales normativos subsaturados:

- `Alcalina` si `Ne >= 1`, `Le >= 1`, o si `SiO2 < 52` con `Alc >= 5`.
- `Subalcalina` si no hay `Ne` ni `Le` normativos y además `Alc < 5` o `SiO2 >= 52`.
- `Transicional` en cualquier otro caso.

### 5.4. Porcentaje de anortita en plagioclasa normativa

La variable `%An en Pl` coincide con:

`An / (An + Ab) * 100`

### 5.5. Suma QAP normativa

La variable `SUM_QAP` corresponde a:

`Q + Ort + Ab + An`

### 5.6. Suma total de minerales normativos

La variable `SUM_CIPW` equivale a la suma de las fases normativas reportadas:

`Q + Cor + Ort + Ab + An + Ne + Le + Kp + Hy + Di + Wo + Ol + La + Ac + Na_ms + Mag + Hem + Ilm + Tit + Ru + Pwk + Ap + Cc + Ft + Py`

## 6. Hallazgos críticos para la interpretación del dataset

### 6.1. El archivo con CIPW incorpora ajustes adicionales

Se detectó que la base enriquecida no solo añade variables, sino que también presenta modificaciones en columnas compartidas. Entre ellas destaca `Rock_Name`, donde se completaron alrededor de `50` registros que en la versión sin CIPW figuraban vacíos.

Este hecho indica que durante la construcción del dataset final se realizaron intervenciones adicionales de curación o imputación litológica. Por tanto, el archivo enriquecido debe tratarse como una versión histórica avanzada del dataset, no como una simple exportación automática.

### 6.2. El campo Quality_Flag no conserva toda la lógica documentada

El documento auxiliar establece una lógica de clasificación de calidad con tres niveles:

- `0`: muestra normal;
- `1`: muestra sospechosa pero utilizable;
- `2`: muestra excluible.

Sin embargo, en el archivo final todas las muestras presentan `Quality_Flag = 0`. Esto sugiere que dicho campo no fue aplicado en su totalidad durante la exportación final, o que el dataset fue previamente filtrado y el indicador terminó homogeneizado.

En consecuencia, esta variable no debe utilizarse sin antes reconstruirla formalmente en el nuevo pipeline.

### 6.3. La variable ITT no es aún completamente trazable

Entre todas las variables revisadas, `ITT` es la que presenta menor claridad metodológica. Aunque en una gran parte de los registros guarda relación con sumas normativas félsicas, no fue posible deducir una fórmula única y estable que reproduzca exactamente todos sus valores.

Esto indica que su definición requiere una revisión específica antes de incorporarse como feature en la nueva versión del proyecto.

## 7. Implicancias para GeoNormML

La principal implicancia metodológica de esta revisión es que el proyecto anterior no adolecía de ausencia de lógica, sino de insuficiente explicitación formal de dicha lógica. Existía una secuencia clara de decisiones geoquímicas, petrológicas y analíticas, pero estas no estaban plenamente encapsuladas en un pipeline reproducible.

Por ello, `GeoNormML` debe adoptar una organización explícita por etapas:

1. `raw_dataset`
2. `clean_dataset`
3. `feature_engineered_dataset`
4. `cipw_dataset`
5. `model_input_dataset`

Cada una de estas capas debe generarse mediante código, con reglas declaradas y auditables. Este cambio no solo mejorará la reproducibilidad, sino también la capacidad de discutir científicamente cada transformación aplicada al dataset.

## 8. Recomendaciones metodológicas inmediatas

Con base en esta revisión, se proponen las siguientes acciones:

- reconstruir en Python todas las variables derivadas ya identificadas;
- utilizar el dataset sin CIPW como base principal de reconstrucción;
- emplear el dataset con CIPW como referencia histórica para verificar consistencia;
- documentar las modificaciones manuales realizadas sobre `Rock_Name`;
- redefinir o auditar formalmente `Quality_Flag`;
- establecer la definición exacta de `ITT` antes de usarla en modelamiento;
- crear un diccionario de datos que registre, para cada columna, su origen, tipo y fórmula de generación.

## 9. Conclusión

La revisión del material disponible demuestra que el flujo de trabajo original fue más rico y estructurado de lo que el informe principal alcanzó a reflejar. El problema central no radicó en una debilidad conceptual del razonamiento, sino en la dispersión de la trazabilidad metodológica entre distintos soportes. La tarea actual de `GeoNormML` consiste, por tanto, en traducir ese conocimiento acumulado a un sistema reproducible en Python, donde cada etapa del dataset pueda reconstruirse, verificarse y discutirse con rigor científico.
