# Modelado Geoespacial e Interpretabilidad SHAP en GeoNormML

Este documento detalla las bases tectónicas de las nuevas características geoespaciales implementadas en src/geonormml/data.py y explica cómo se utiliza el análisis SHAP para aportar transparencia geológica al pipeline de clasificación.

---

## 1. Bases Geotectónicas de las Características Espaciales

El magmatismo ígneo en el Perú está controlado por la subducción de la placa de Nazca bajo la placa Sudamericana. Las variaciones espaciales en la geoquímica de roca total responden a dos ejes principales:

### A. Distancia a la Fosa Peruano-Chilena (Trench_Dist) - Eje Transversal (Across-Arc)
La fosa representa el punto de inicio de la subducción. Conforme la placa oceánica subduce hacia el este, aumenta su profundidad. La distancia horizontal a la fosa controla:
* **La profundidad del slab (Zona de Benioff):** Determina las condiciones de presión y temperatura a las que se liberan los fluidos hidratados del slab que inducen la fusión parcial de la cuña mantélica.
* **El espesor de la corteza continental continental (Efecto de Dickinson / Relación K-h):** Clásicamente, a mayor distancia de la fosa, los magmas experimentan un mayor trayecto a través de una corteza más gruesa, lo que favorece procesos de asimilación y cristalización fraccionada (MASH). Esto incrementa sistemáticamente las relaciones de elementos incompatibles (como el potasio $\text{K}_2\text{O}$ normativo en la serie magmática, pasando de series de bajo potasio, a calcoalcalinas de medio/alto potasio y shoshoníticas en el tras-arco).

#### Método de Cálculo:
La trinchera peruana se aproximó geométricamente mediante segmentos lineales definidos por 9 vértices clave que siguen la curvatura del margen continental peruano:
1. Norte (cerca de Piura): $(-82.0^\circ, -4.0^\circ)$
2. Centro-Norte (Ancash): $(-80.0^\circ, -10.0^\circ)$
3. Centro (Lima): $(-78.5^\circ, -12.0^\circ)$
4. Sur (Arequipa-Tacna): $(-72.0^\circ, -20.0^\circ)$

La distancia geodésica mínima de cada muestra georreferenciada a esta línea se calcula en grados decimales y se convierte a kilómetros (asumiendo un promedio de $111.12\text{ km/grado}$ en la región).

### B. Latitud (LAT) - Eje Longitudinal (Along-Arc)
El margen andino peruano está segmentado latitudinalmente debido a la geometría de la subducción:
* **Subducción Plana ("Flat-slab") en el Centro-Norte (latitudes $\sim 5^\circ\text{ S}$ a $14^\circ\text{ S}$):** La placa subduce con un ángulo muy bajo, lo que inhibe el vulcanismo cuaternario activo debido a la ausencia de cuña mantélica a profundidades óptimas. Aquí dominan los afloramientos plutónicos mesozoicos a miocenos del Batolito de la Costa y de la Cordillera Blanca.
* **Subducción Inclinada ("Normal/Steep-slab") en el Sur (latitudes $\sim 15^\circ\text{ S}$ a $18^\circ\text{ S}$):** Permite una cuña de manto activa, albergando la Zona Volcánica Central (ZVC) de los Andes, con vulcanismo activo del Plio-Pleistoceno (Grupo Barroso).

Introducir LAT como feature permite al modelo ajustar los límites de decisión geoquímica basándose en esta segmentación termomecánica natural de los Andes peruanos.

---

## 2. Explicabilidad Física mediante Valores SHAP

Los modelos de inteligencia artificial tradicionales a menudo sufren del problema de "caja negra". En geociencias, es fundamental entender **por qué** un modelo clasifica una muestra bajo un nombre litológico específico.

Para resolver esto, implementamos el cálculo de **valores SHAP (SHapley Additive exPlanations)**, basados en la teoría de juegos cooperativos. SHAP calcula la contribución exacta (aditiva) de cada variable en el score de predicción de la clase de roca para cada muestra.

### A. Explicabilidad Global (SHAP Bar Plot)
Permite ordenar las variables según su impacto absoluto promedio en todas las clases litológicas del dominio. Nos dice cuáles son las features que estructuran la clasificación general en el territorio peruano.

### B. Explicabilidad Detallada por Litología (Summary Beeswarm Plot)
El gráfico Beeswarm combina la importancia de las features con el sentido del impacto:
* **Eje Y:** Ordena las variables por importancia.
* **Eje X (SHAP Value):** Puntos a la derecha (SHAP $> 0$) indican que esa variable empuja la predicción hacia la clase objetivo. Puntos a la izquierda (SHAP $< 0$) la alejan.
* **Código de Color (Feature Value):** Rojo para valores altos de la variable, azul para valores bajos.

#### Ejemplo de Interpretación Geológica (Clase Riolita y Granito):
* Si el modelo evalúa la clase **riolita** o **granito**:
  * Esperamos que valores altos de cuarzo normativo ($\text{Q}$), ortoclasa normativa ($\text{Or}$) y $\text{SiO}_2$ (puntos rojos) tengan valores SHAP fuertemente positivos (a la derecha), empujando al modelo a clasificar la roca como ácida.
  * Esperamos que el índice de color normativo ($\text{ICN}$) o el magnesio (Mg#) tengan puntos rojos a la izquierda (valores altos alejan la predicción de ser un granito/riolita) y puntos azules a la derecha (valores bajos favorecen la clasificación de roca ácida).
  * La inclusión de Trench_Dist y LAT mostrará si la pertenencia geográfica y la distancia a la fosa discriminan de forma secundaria ciertas facies ígneas evolutivas específicas.
