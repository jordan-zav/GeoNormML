# Trazabilidad del Dataset y Flujo de Ingeniería de Variables en GeoNormML

## 1. Propósito del documento

Este documento formaliza la lógica real seguida en la construcción del dataset usado en el proyecto de clasificación litológica de rocas ígneas. Su objetivo es distinguir con claridad entre:

- variables originales provenientes de las fuentes de datos;
- variables derivadas calculadas durante el preprocesamiento;
- variables normativas CIPW obtenidas a partir de los óxidos mayores;
- variables objetivo y columnas ajustadas manualmente durante la curación del dataset.

La necesidad de este documento surge porque en la versión previa del proyecto parte de la lógica metodológica quedó distribuida entre el paper, hojas de cálculo, reglas implícitas en Excel y criterios complementarios consignados en `Considerations.docx`. En consecuencia, este texto busca convertir esa lógica en una estructura metodológica explícita, reproducible y útil para la nueva implementación en Python.

## 2. Versiones del dataset identificadas

Dentro de la carpeta [`Dataset`](/I:/GDrive/Projects/In%20Development/GeoNormML/Dataset) se identifican dos versiones principales del dataset:

### 2.1. Dataset base

Archivo: [`0. Final_Dataset.xlsx`](/I:/GDrive/Projects/In%20Development/GeoNormML/Dataset/0.%20Final_Dataset.xlsx)

Características:

- Contiene `2707` muestras.
- Tiene `28` columnas.
- Representa una versión depurada del dataset final, pero aún sin minerales normativos CIPW.
- Tampoco incluye varias variables derivadas calculadas posteriormente a partir de las columnas originales.

Interpretación metodológica:

Esta versión no debe entenderse como “dataset completamente crudo”, sino como una base curada y lista para enriquecerse con nuevas variables. Es, en términos prácticos, el punto de partida para la ingeniería de variables reproducible en Python.

### 2.2. Dataset enriquecido con CIPW

Archivo: [`0. Final_Dataset+CIPW.xlsx`](/I:/GDrive/Projects/In%20Development/GeoNormML/Dataset/0.%20Final_Dataset%2BCIPW.xlsx)

Características:

- Contiene también `2707` muestras.
- Tiene `62` columnas.
- Incluye minerales normativos CIPW.
- Incluye variables derivadas adicionales calculadas a partir de óxidos y columnas normativas.
- Corresponde a una versión más avanzada del pipeline, cercana al insumo final utilizado para modelamiento.

Interpretación metodológica:

Esta versión refleja una etapa posterior de transformación del dataset. No solo agrega CIPW, sino también variables auxiliares, indicadores geoquímicos y algunos ajustes en columnas compartidas, por lo que no debe interpretarse como una simple extensión mecánica del archivo base.

## 3. Estructura conceptual del flujo de datos

La lógica real del proyecto puede representarse en cinco capas:

### 3.1. Capa 1: dataset base curado

Incluye:

- identificadores;
- fuente de procedencia;
- coordenadas;
- metadatos litológicos;
- óxidos mayores;
- LOI.

Esta capa contiene la información principal consolidada tras la depuración inicial y constituye el insumo mínimo para posteriores transformaciones.

### 3.2. Capa 2: dataset con variables derivadas geoquímicas

Incluye variables obtenidas directamente de los óxidos y otras columnas primarias, por ejemplo:

- `Sum_Oxs`
- `Clase_SiO2`
- `Alc`
- `Serie_Mag`
- `Quality_Flag`

Estas variables no pertenecen a la base original, sino a una etapa de feature engineering geoquímico.

### 3.3. Capa 3: dataset con minerales normativos CIPW

Incluye los minerales normativos y otros productos del cálculo CIPW, tales como:

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

Esta capa depende del cálculo normativo y representa el núcleo petroquímico del proyecto.

### 3.4. Capa 4: dataset con métricas derivadas de CIPW

Incluye variables construidas a partir de los resultados normativos, por ejemplo:

- `%An en Pl`
- `SUM_QAP`
- `SUM_CIPW`
- `ITT`

Estas variables sintetizan relaciones internas entre minerales normativos y sirven como descriptores adicionales para clasificación.

### 3.5. Capa 5: dataset final para modelamiento

Esta capa combina:

- variables originales;
- variables derivadas geoquímicas;
- minerales CIPW;
- métricas derivadas;
- variable objetivo litológica.

Es la capa que debe alimentarse a los modelos de machine learning, idealmente a través de pipelines controlados y reproducibles.

## 4. Inventario de variables por origen

### 4.1. Variables originales

Estas columnas proceden del dataset base y corresponden a datos primarios o metadatos conservados durante la depuración:

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

Estas columnas fueron añadidas posteriormente mediante reglas o fórmulas:

- `Sum_Oxs`
- `Clase_SiO2`
- `Alc`
- `Serie_Mag`
- `Quality_Flag`

### 4.3. Variables normativas CIPW

Corresponden al cálculo normativo:

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

## 5. Reglas identificadas y ya trazables

Con base en el archivo [`Considerations.docx`](/I:/GDrive/Projects/In%20Development/GeoNormML/Dataset/Considerations.docx) y en las fórmulas observadas en Excel, fue posible identificar las siguientes reglas:

### 5.1. Clase_SiO2

Clasificación basada en el contenido de sílice:

- `SiO2 >= 63` → `Ácida`
- `52 <= SiO2 < 63` → `Intermedia`
- `45 <= SiO2 < 52` → `Básica`
- `SiO2 < 45` → `Ultramáfica`

### 5.2. Alc

Fórmula:

`Alc = Na2O + K2O`

### 5.3. Serie_Mag

Regla conceptual identificada:

- `Alcalina` si la muestra contiene `Ne >= 1`, `Le >= 1`, o si `SiO2 < 52` y `Alc >= 5`.
- `Subalcalina` si no contiene `Ne` ni `Le` normativos y además `Alc < 5` o `SiO2 >= 52`.
- `Transicional` en cualquier otro caso.

### 5.4. %An en Pl

Fórmula validada:

`%An en Pl = An / (An + Ab) * 100`

### 5.5. SUM_QAP

Fórmula validada:

`SUM_QAP = Q + Ort + Ab + An`

### 5.6. SUM_CIPW

Corresponde a la suma de todos los minerales normativos reportados en el archivo final:

`Q + Cor + Ort + Ab + An + Ne + Le + Kp + Hy + Di + Wo + Ol + La + Ac + Na_ms + Mag + Hem + Ilm + Tit + Ru + Pwk + Ap + Cc + Ft + Py`

## 6. Hallazgos metodológicos relevantes

### 6.1. El dataset enriquecido no es una simple extensión

Aunque ambos archivos contienen las mismas `2707` muestras, el archivo con CIPW no solo añade columnas nuevas. Se detectaron cambios adicionales en columnas compartidas, especialmente en `Rock_Name`, donde se completaron aproximadamente `50` registros que aparecían vacíos en la base sin CIPW.

Implicancia:

El dataset con CIPW debe considerarse una versión curada adicionalmente, no una mera ampliación automática.

### 6.2. Quality_Flag no refleja toda la lógica escrita en Considerations

Según el archivo auxiliar, `Quality_Flag` debía marcar:

- `2` para muestras excluibles;
- `1` para muestras sospechosas pero utilizables;
- `0` para muestras normales.

Sin embargo, en la versión final del Excel todas las filas tienen `Quality_Flag = 0`.

Implicancia:

O bien la regla nunca fue aplicada en la exportación final, o bien la base ya fue filtrada previamente y el campo quedó homogeneizado. En cualquier caso, esta columna no debe asumirse como validación automática plenamente activa sin reconstruir su cálculo en Python.

### 6.3. ITT requiere redefinición formal

La variable `ITT` no pudo reconstruirse de manera completamente consistente con una sola fórmula simple. En muchos casos coincide con combinaciones de minerales félsicos, pero en otras filas presenta diferencias apreciables.

Implicancia:

Antes de usarla como feature en `GeoNormML`, se debe:

- rastrear su definición original exacta;
- verificar si fue editada manualmente;
- decidir si se conserva, se redefine o se elimina.

## 7. Interpretación metodológica para GeoNormML

La principal conclusión es que el proyecto anterior sí poseía una lógica metodológica clara, pero esta quedó distribuida entre distintos soportes y no completamente explicitada. La debilidad no estuvo en la intuición geológica ni en la estructura general del trabajo, sino en la falta de trazabilidad computacional de varios pasos intermedios.

Por ello, en `GeoNormML` el dataset debe organizarse explícitamente en etapas:

1. `raw_dataset`
2. `clean_dataset`
3. `feature_engineered_dataset`
4. `cipw_dataset`
5. `model_input_dataset`

Cada etapa debe poder reconstruirse desde código, con reglas documentadas, sin depender de operaciones manuales en Excel.

## 8. Recomendaciones inmediatas

- Implementar en Python todas las variables derivadas ya identificadas.
- Usar el archivo sin CIPW como base de reconstrucción reproducible.
- Tomar el archivo con CIPW como referencia histórica para validación cruzada del pipeline.
- Registrar explícitamente las modificaciones manuales en `Rock_Name`.
- Auditar `Quality_Flag` y `ITT` antes de incorporarlos al modelado final.
- Mantener una tabla de metadatos por columna con:
  - nombre;
  - tipo de variable;
  - origen;
  - fórmula o regla;
  - etapa del pipeline en que se genera.

## 9. Cierre

La existencia de múltiples capas de transformación no es una debilidad en sí misma; al contrario, refleja un trabajo de curación y razonamiento geoquímico significativo. La mejora necesaria consiste en traducir esas capas a un pipeline reproducible, trazable y auditable. Ese será precisamente uno de los aportes centrales de `GeoNormML`.
