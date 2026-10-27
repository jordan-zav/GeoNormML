# Revisión de la distribución de `ROCK_NAME` en `Merge_Filtered`

## Archivos revisados

- [`Merge_Filtered.xlsx`](/I:/GDrive/Projects/In%20Development/GeoNormML/Dataset/Filtered/Merge_Filtered.xlsx)
- [`Informe de Proyecto 2025-II .pdf`](/I:/GDrive/Projects/Done/ABET%202025/documentacion/Informe%20de%20Proyecto%202025-II%20.pdf)

## Respaldo realizado

Antes de cualquier procesamiento adicional se creó un backup del archivo original:

- [`Merge_Filtered_20260404_012537.xlsx`](/I:/GDrive/Projects/In%20Development/GeoNormML/Dataset/backup/Merge_Filtered_20260404_012537.xlsx)

## Resumen del dataset revisado

La hoja `merge` contiene:

- `3144` filas
- `30` columnas
- `3136` valores no nulos en `ROCK_NAME`
- `8` valores nulos en `ROCK_NAME`
- `156` etiquetas únicas no nulas en `ROCK_NAME`

## Hallazgos principales sobre `ROCK_NAME`

La distribución de nombres es altamente heterogénea y todavía corresponde a una fase previa a la estandarización final. Los principales problemas observados son:

### 1. Mezcla de idiomas

Coexisten etiquetas en inglés y español, por ejemplo:

- `ANDESITE`
- `andesita`
- `DACITE`
- `dacita`
- `GRANITE`
- `granito`

Esto fragmenta artificialmente la frecuencia real de las clases.

### 2. Inconsistencia de capitalización

Se identificó una mezcla fuerte entre mayúsculas y minúsculas:

- `1793` registros en mayúsculas
- `1340` registros en minúsculas

Esto confirma que aún no se ha aplicado una normalización de estilo.

### 3. Minerales embebidos en el nombre litológico

Muchas etiquetas incluyen minerales o descriptores mineralógicos dentro de `ROCK_NAME`, por ejemplo:

- `ANDESITE, OLIVINE`
- `ANDESITE, HORNBLENDE-AUGITE`
- `DIORITE, QUARTZ-HORNBLENDE`

Esto apoya tu observación de que una parte del contenido de `ROCK_NAME` debería moverse a una columna separada como `MIN`.

### 4. Etiquetas ambiguas tipo `A / B`

Se detectaron `245` registros con `/`, lo cual indica nombres dobles, nombres alternativos o combinaciones ambiguas:

- `ANDESITE / NOT GIVEN`
- `RHYOLITE / IGNIMBRITIC TUFF`
- `DACITE / ANDESITE`
- `LATITE / TRACHYANDESITE`

Esto coincide con tu estrategia previa de colocar el nombre dominante en `ROCK_NAME` y el secundario en `SEC_ROCK_NAME`.

### 5. Presencia de `NOT GIVEN`

Se detectaron `118` registros con la cadena `NOT GIVEN`, lo cual introduce ruido semántico y no debe permanecer como parte del target principal.

### 6. Cola larga de clases raras

La distribución presenta una cola larga muy marcada:

- `56` etiquetas aparecen una sola vez
- `76` etiquetas aparecen una o dos veces
- `101` etiquetas aparecen cinco veces o menos
- `111` etiquetas aparecen menos de diez veces
- `124` etiquetas aparecen menos de veinte veces

Esto implica que, en su estado actual, `ROCK_NAME` no es todavía una variable objetivo estable para entrenamiento supervisado.

## Clases más frecuentes observadas

Las principales etiquetas detectadas fueron:

- `ANDESITE`: `545`
- `andesita`: `302`
- `DACITE`: `232`
- `diorita`: `179`
- `granodiorita`: `148`
- `GRANITE`: `123`
- `GRANODIORITE`: `105`
- `RHYOLITE`: `104`
- `dacita`: `78`
- `ANDESITE / NOT GIVEN`: `77`
- `basalto`: `77`
- `BASALTIC-ANDESITE`: `74`

Esto muestra con claridad que la clase real dominante probablemente sea andesita, pero su frecuencia actual está repartida entre múltiples variantes ortográficas y semánticas.

## Interpretación metodológica

La distribución observada respalda completamente la lógica que describiste para tu proceso de curación:

1. Traducir nombres del inglés al español.
2. Separar minerales y descriptores mineralógicos desde `ROCK_NAME` hacia una columna `MIN`.
3. Resolver etiquetas ambiguas `A / B` asignando la litología dominante a `ROCK_NAME`.
4. Conservar la litología secundaria en `SEC_ROCK_NAME`.
5. Usar `SEC_ROCK_NAME` como feature contextual en lugar de incorporarla directamente al target principal.

Desde el punto de vista de machine learning y trazabilidad, esta decisión es metodológicamente sólida porque:

- reduce la fragmentación artificial de clases;
- mejora la consistencia del target;
- preserva información secundaria útil;
- evita perder contenido litológico relevante durante la estandarización.

## Información adicional recuperada del informe sobre filtros de depuración

El informe sí contiene criterios adicionales útiles para la etapa de depuración. Los más relevantes son:

### 1. Unificación lingüística y target

El informe indica explícitamente que:

- se tradujeron y estandarizaron los nombres a un formato coherente en español;
- se separó el nombre en `Rock_Name` y `Sec_Rock_Name`;
- `Rock_Name` quedó como litología principal;
- `Sec_Rock_Name` se preservó como descriptor secundario;
- litologías ambiguas o texturales, como tobas, fueron reclasificadas hacia equivalentes composicionales.

### 2. Umbrales geoquímicos aplicados

Se documentan los siguientes filtros:

- `SiO2`: `35–82 wt.%`
- `Na2O` y `K2O`: `>= 0.05 wt.%`
- `Na2O + K2O`: `0.5–13.5 wt.%`
- `P2O5`: `<= 2.5 wt.%`
- `Sum_Oxs`: `90–110 %`

### 3. Criterios con LOI

Se usó `LOI` como indicador de alteración:

- rango normal aproximado: `-0.5 % < LOI < 4 %`
- `LOI > 4–5 %` como señal de alteración relevante
- `LOI < -0.5 %` como posible error analítico

### 4. Exclusión de composiciones incompatibles

El informe menciona revisiones caso por caso para muestras químicamente contradictorias, por ejemplo:

- basaltos con `SiO2` excesivamente alto;
- dioritas con alcalinidad incompatible;
- muestras con alteración o meteorización evidente.

### 5. Agrupación de clases con baja frecuencia

Las litologías con menos de `10` muestras fueron agrupadas dentro de familias mayores. El informe menciona ejemplos como:

- `Monzogabro` -> `Gabro`
- `Dolerita` -> `Gabro`
- `Sienita` -> `Monzonita`
- `Traquibasalto` -> `Basalto`
- `Basanita` -> `Basalto`
- `Traquita` -> `Riodacita`

## Archivos generados para esta revisión

Se generaron los siguientes productos auxiliares:

- [`rock_name_frequency.csv`](/I:/GDrive/Projects/In%20Development/GeoNormML/Dataset/Filtered/analysis/rock_name_frequency.csv)
- [`rock_name_distribution_summary.txt`](/I:/GDrive/Projects/In%20Development/GeoNormML/Dataset/Filtered/analysis/rock_name_distribution_summary.txt)
- [`rock_name_histogram_top30.png`](/I:/GDrive/Projects/In%20Development/GeoNormML/Dataset/Filtered/analysis/rock_name_histogram_top30.png)
- [`rock_name_label_frequency_hist.png`](/I:/GDrive/Projects/In%20Development/GeoNormML/Dataset/Filtered/analysis/rock_name_label_frequency_hist.png)

## Conclusión

Antes de continuar con `Merge_Filtered`, la principal prioridad no es todavía el modelado, sino la normalización semántica de `ROCK_NAME`. La evidencia revisada confirma que el target litológico aún está demasiado fragmentado por idioma, formato, ambigüedad y presencia de minerales dentro del nombre. Tu estrategia previa de traducir, separar minerales, distinguir nombre principal y secundario, y agrupar clases raras está plenamente justificada y además es consistente con la lógica descrita en el informe.
