# Índices Petrológicos Adicionales en GeoNormML

Este documento describe la base geológica, las fórmulas de cálculo y la interpretación física de las nuevas variables petrológicas añadidas al pipeline reproducible en src/geonormml/data.py e integradas en el conjunto de variables combined_enriched.

---

## 1. Índice de Saturación de Alúmina (ASI / Shand's Index)

El **Índice de Saturación de Alúmina (ASI)**, propuesto originalmente por Shand (1943), es el indicador petroquímico por excelencia para clasificar el estado de saturación en alúmina de rocas félsicas a intermedias.

### Fórmula Molar:
$$\text{ASI} = \frac{\text{Al}_2\text{O}_3}{\text{CaO} + \text{Na}_2\text{O} + \text{K}_2\text{O}} \quad (\text{en base molar})$$

Para obtener los moles a partir de los óxidos expresados en porcentaje en peso (wt.%), se divide cada óxido entre su respectivo peso molecular:
* $\text{mol\_Al}_2\text{O}_3 = \frac{\text{Al}_2\text{O}_3}{101.96}$
* $\text{mol\_CaO} = \frac{\text{CaO}}{56.08}$
* $\text{mol\_Na}_2\text{O} = \frac{\text{Na}_2\text{O}}{61.98}$
* $\text{mol\_K}_2\text{O} = \frac{\text{K}_2\text{O}}{94.20}$

### Significado e Interpretación Geológica:
* **ASI > 1.0 (Peraluminosas):** La roca posee un exceso de alúmina que no puede ser acomodado únicamente en feldespatos (donde la relación $\text{Al}:(\text{Ca}, \text{Na}, \text{K})$ es $1:1$). Esto se traduce en la presencia de minerales normativos como el **corindón (Cor)** o minerales modales ricos en alúmina (biotita, muscovita, granate, cordierita o silimanita). Es típico de granitos de tipo S (derivados de la fusión de sedimentos).
* **ASI < 1.0 y $\frac{\text{Al}_2\text{O}_3}{\text{Na}_2\text{O} + \text{K}_2\text{O}} > 1.0$ (Metaluminosas):** Rocas típicas de arcos magmáticos (granitos tipo I, andesitas, dacitas). Tienen suficiente $\text{Ca}$ para formar plagioclasas y minerales máficos cálcicos como la hornblenda o el clinopiroxeno.
* **$\frac{\text{Al}_2\text{O}_3}{\text{Na}_2\text{O} + \text{K}_2\text{O}} < 1.0$ (Peralkalinas):** Rocas extremadamente ricas en álcalis respecto a la alúmina. Se forman minerales normativos de sodio como el piroxeno alcalino **egirina (Ac)** y anfíboles alcalinos. Es característico de magmatismo de intraplaca o rifts.

---

## 2. Número de Magnesio (Mg# / Mg-number)

El **Mg#** representa la relación molar entre el magnesio y el hierro ferroso total. Es el principal indicador de la evolución de un magma por cristalización fraccionada o del carácter primario de un fundido máfico.

### Fórmula Molar:
$$\text{Mg\#} = \frac{\text{mol\_MgO}}{\text{mol\_MgO} + \text{mol\_FeOT}} \times 100$$

Pesos moleculares utilizados:
* $\text{mol\_MgO} = \frac{\text{MgO}}{40.30}$
* $\text{mol\_FeOT} = \frac{\text{FeOT}}{71.85}$

### Significado e Interpretación Geológica:
* **Mg# > 65–70 (Magmas Primarios / Manto):** Valores muy altos indican magmas que se encuentran en equilibrio químico directo con un manto peridotítico sin haber sufrido fraccionamiento significativo de olivino o piroxenos.
* **Mg# < 50 (Magmas Evolucionados):** Reflejan procesos continuos de cristalización fraccionada donde el magnesio es removido rápidamente del fundido en fases tempranas (olivino, piroxenos), enriqueciendo residualmente al magma en hierro y sílice (p. ej., dacitas, riolitas).

---

## 3. Índice de Diferenciación de Thornton-Tuttle (DI_Tuttle)

Desarrollado por Thornton y Tuttle (1960), representa la suma de los minerales normativos ideales que componen el "sistema petrogénico residual" (el mínimo del sistema granítico).

### Fórmula Normativa:
$$\text{DI\_Tuttle} = \text{Q} + \text{Or} + \text{Ab} + \text{Ne} + \text{Kp} + \text{Le}$$

*(Donde todos los términos son los porcentajes en peso de los minerales normativos calculados).*

### Significado e Interpretación Geológica:
* El índice cuantifica el grado de diferenciación de una roca magmática hacia composiciones de alta temperatura residuales (el sistema $\text{SiO}_2-\text{NaAlSiO}_4-\text{KAlSiO}_4$).
* Varía desde valores muy bajos ($< 20$) en rocas básicas/ultramáficas (como gabros y basaltos) hasta valores cercanos a $100$ en rocas félsicas altamente diferenciadas (como riolitas y granitos alcalinos).

---

## 4. Índice de Color Normativo (ICN)

El **ICN** es un estimador del índice de color petrográfico clásico de las rocas ígneas, calculado a partir de la suma de los minerales normativos fémeos (máficos) y óxidos metálicos.

### Fórmula Normativa:
$$\text{ICN} = \text{Di} + \text{Hd} + \text{Wo} + \text{En} + \text{Fs} + \text{Fo} + \text{Fa} + \text{Mt} + \text{Hm} + \text{Ilm} + \text{Ru}$$

### Significado e Interpretación Geológica:
* Clasifica las muestras en términos de su leucocracia o melanocracia teórica:
  * **Leucocráticas (ICN < 30):** Rocas félsicas y ácidas dominadas por cuarzo y feldespatos (granito, riolita).
  * **Mesocráticas (30 < ICN < 60):** Rocas intermedias (diorita, andesita).
  * **Melanocráticas (60 < ICN < 90):** Rocas básicas (basalto, gabro).
  * **Ultramáficas (ICN > 90):** Rocas compuestas casi en su totalidad por piroxenos y olivino normativos.
