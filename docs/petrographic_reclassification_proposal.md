# Propuesta de Reclasificación Petrográfica de Clases Raras

## Propósito

Este documento propone una tabla preliminar de reclasificación para clases litológicas raras del dataset normalizado de [`Merge_Filtered_name_normalized.xlsx`](/I:/GDrive/Projects/In%20Development/GeoNormML/Dataset/Filtered/processed/Merge_Filtered_name_normalized.xlsx).

La propuesta **no debe aplicarse todavía**. Su objetivo es separar tres escenarios:

- clases que sí parecen tener una clase vecina clara y justificable;
- clases cuya cercanía petrográfica existe, pero la fusión sigue siendo una inferencia simplificadora;
- clases que no deben fusionarse todavía sin revisar química, textura o contexto.

## Base de trabajo

Esta propuesta se apoya en:

- la frecuencia actual de clases en el dataset normalizado;
- tu criterio previo de estabilizar clases con muy baja frecuencia;
- la lógica petrográfica descrita en el informe;
- referencias externas para confirmar vecindades taxonómicas o equivalencias.

## Fuentes consultadas

- [BGS Rock Classification Scheme – Vol 1 – Igneous](https://www.bgs.ac.uk/download/bgs-rock-classification-scheme-igneous/)
- [Ontario Rock Nomenclature Standard (GeoOntario PDF)](https://prd-0420-geoontario-0000-blob-cge0eud7azhvfsf7.z01.azurefd.net/lrc-geology-documents/publication/OFR6289/OFR6289.pdf)
- [USGS / North American Volcanic Science Language Appendix](https://pubs.usgs.gov/of/2004/1451/sltt/appendixD/appendixD.pdf)
- [NPS Igneous Rocks Overview](https://home.nps.gov/subjects/geology/igneous.htm)
- [USGS Pitchstone Plateau rhyolite](https://www.usgs.gov/media/images/pitchstone-plateau-yellowstone-rhyolite-sanidine)

## Resumen de criterio

### Nivel A: mapeo fuerte

Clases donde existe una relación bastante clara de sinonimia, equivalencia composicional reconocida o proximidad taxonómica fuerte.

### Nivel B: mapeo tentativo

Clases donde la fusión puede ser útil para estabilizar el target, pero sigue siendo una simplificación.

### Nivel C: no fusionar aún

Clases donde la decisión correcta depende de química, textura, protolito o revisión manual.

## Propuesta por clase

| Clase actual | n | Propuesta | Nivel | Justificación |
|---|---:|---|---|---|
| `aplita` | 1 | `granito` | A | La aplita es una roca intrusiva fina, usualmente de composición granítica o muy próxima a granito. |
| `basanita` | 1 | `basalto` | B | Es una roca máfica alcalina distinta, pero en esquemas simplificados queda cerca del extremo basáltico. |
| `mugearita` | 1 | `traquiandesita basaltica` | A | La mugearita es un subtipo de basaltic trachyandesite. |
| `dolerita` | 1 | `gabro` | A | BGS trata dolerita/diabase como equivalente de microgabbro y recomienda usar `gabbro` como raíz. |
| `pitchstone` | 1 | `riolita` | A | El pitchstone revisado por USGS corresponde a flujo riolítico; tu normalización ya lo acerca a riolita. |
| `metatonalita` | 2 | `tonalita` | A | El prefijo `meta-` remite al protolito tonalítico; útil si el objetivo es litología ígnea original. |
| `adamelita` | 3 | `monzogranito` | A | USGS usa `monzogranite [adamellite]`; es el mapeo más sólido. |
| `monzogabro` | 3 | `gabro` | B | QAPF lo ubica muy próximo a gabbro/monzodiorite; para simplificar, `gabro` es la fusión más razonable. |
| `ortogranito` | 4 | `granito` | A | Si se está recuperando el protolito ígneo, el nombre raíz es granito. |
| `basalto calcoalcalino` | 6 | `basalto` | B | Es una variante de serie magmática, no un root name distinto del basalto. |
| `sienita` | 6 | `monzonita` | B | Syenite y monzonite son campos vecinos en QAPF; tu paper ya usó esta simplificación. |
| `traquibasalto` | 9 | `basalto` | B | Trachybasalt es más alcalino que basalt, pero sigue siendo el vecino simplificado más cercano. |
| `basalto alcalino` | 10 | `basalto` | B | Sigue siendo una variedad de basalt definida por alcalinidad. |
| `metamonzogranito` | 21 | `monzogranito` | A | Misma lógica que `metatonalita`: si el objetivo es recuperar la litología ígnea base, el root name es monzogranito. |

## Clases que recomiendo no fusionar todavía

| Clase actual | n | Recomendación | Motivo |
|---|---:|---|---|
| `lamproita` | 3 | No fusionar aún | Lamproite no es simplemente equivalente a lamprophyre; requiere decisión geológica explícita. |
| `lamprofiro` | 7 | No fusionar aún | Puede tener cercanías químicas con shoshonita, latita o trachybasalt, pero no conviene imponerlo solo por nombre. |
| `traquiandesita` | 7 | No fusionar aún | Es una clase válida; `latita` y `benmoreita` son subtipos, pero no toda traquiandesita equivale a latita. |
| `traquita` | 10 | No fusionar aún | Está cerca de `traquidacita` y del extremo silícico alcalino; fusionarla con `riodacita` o `riolita` es una simplificación fuerte. |
| `traquidacita` | 3 | No fusionar aún | Está cerca de `traquita` y también del extremo riolítico; conviene decidir con química. |
| `porfido` | 1 | No fusionar aún | `Porfido` es textura/genérico, no nombre composicional suficiente. |

## Clases texturales que deberían decidirse con química o contexto

| Clase actual | n | Recomendación |
|---|---:|---|
| `toba` | 12 | Reasignar por composición a una litología equivalente, no por nombre |
| `toba cristalina` | 38 | Reasignar por composición |
| `toba litica` | 10 | Reasignar por composición |
| `toba vitrea` | 14 | Reasignar por composición |
| `tufo` | 4 | Reasignar por composición |
| `tufo de cristales` | 1 | Reasignar por composición |

Tu informe ya documenta este criterio: las tobas ambiguas o texturales fueron reclasificadas hacia equivalentes composicionales como andesita, dacita o riolita.

## Clases que deberían excluirse o revisarse aparte

| Clase actual | n | Recomendación | Motivo |
|---|---:|---|---|
| `gneis` | 2 | Excluir o separar | Metamórfica |
| `esquisto` | 2 | Excluir o separar | Metamórfica |
| `anfibolita` | 1 | Excluir o separar | Metamórfica |
| `arenisca tobacea` | 1 | Excluir o separar | Sedimentaria/volcanosedimentaria, no root ígneo limpio |

## Observaciones importantes

### 1. `adamelita -> monzogranito` es una de las conversiones mejor respaldadas

La evidencia consultada muestra uso explícito de `monzogranite [adamellite]` en documentación de USGS. Esta es una buena candidata para un mapeo definitivo.

### 2. `mugearita -> traquiandesita basaltica` también es un mapeo fuerte

La literatura consultada la trata como subtipo de `basaltic trachyandesite`, por lo que aquí la fusión no es arbitraria.

### 3. `dolerita -> gabro` tiene muy buen respaldo operativo

La referencia de Ontario/BGS la trata como equivalente de diabase/microgabbro y recomienda usar `gabbro` como raíz.

### 4. Las rocas piroclásticas no deberían fusionarse solo por nombre

`Toba`, `tufo` y variantes similares son nombres de textura o modo de emplazamiento. Si se reclasifican, lo correcto es hacerlo según composición geoquímica o equivalencia composicional.

### 5. `lamproita` y `lamprofiro` merecen una decisión aparte

Aunque en un flujo práctico pueden terminar agrupándose para evitar clases demasiado pequeñas, la búsqueda no respalda tratarlas como equivalentes petrográficos directos. Si se fusionan, conviene documentarlo como decisión pragmática del target, no como equivalencia estricta.

## Recomendación operativa

Antes de ejecutar reclasificaciones finales, sugiero separar la decisión en tres tablas:

1. `mapeos_confirmados`
2. `mapeos_tentativos`
3. `clases_a_excluir_o_revisar`

De ese modo, cuando apliquemos la reclasificación final, sabremos distinguir entre:

- equivalencias razonablemente aceptadas;
- simplificaciones metodológicas para estabilizar clases;
- exclusiones por incompatibilidad litológica con el objetivo del modelo.
