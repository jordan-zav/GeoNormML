# Bootstrap del Pipeline de Modelado

## Dataset oficial

El dataset oficial de entrenamiento es:

- [`Merge_Filtered_training_ready_v1.xlsx`](/I:/GDrive/Projects/In%20Development/GeoNormML/Dataset/Filtered/final/Merge_Filtered_training_ready_v1.xlsx)

## Estructura creada

- [`src/geonormml/config.py`](/I:/GDrive/Projects/In%20Development/GeoNormML/src/geonormml/config.py)
- [`src/geonormml/data.py`](/I:/GDrive/Projects/In%20Development/GeoNormML/src/geonormml/data.py)
- [`src/geonormml/features.py`](/I:/GDrive/Projects/In%20Development/GeoNormML/src/geonormml/features.py)
- [`src/geonormml/split.py`](/I:/GDrive/Projects/In%20Development/GeoNormML/src/geonormml/split.py)
- [`scripts/build_modeling_artifacts.py`](/I:/GDrive/Projects/In%20Development/GeoNormML/scripts/build_modeling_artifacts.py)

## Qué hace

Este bootstrap deja listo:

- cargador del dataset oficial;
- definición de tres conjuntos de entrada:
  - `oxides`
  - `cipw`
  - `combined`
- validación de columnas esperadas;
- partición holdout estratificada reproducible;
- folds estratificados reproducibles para validación cruzada;
- manifiestos de features y frecuencia del target.

## Salidas esperadas

Al ejecutar:

```powershell
$env:PYTHONPATH='I:\GDrive\Projects\In Development\GeoNormML\src'
python scripts\build_modeling_artifacts.py
```

se generan archivos en `artifacts/` con:

- `feature_sets.csv`
- `target_frequency.csv`
- `holdout_split.json`
- `cv_folds.json`
- `modeling_artifacts_summary.txt`

## Nota metodológica

Este paso no entrena modelos todavía. Su función es fijar una base reproducible para que los siguientes scripts comparen exactamente los mismos targets, splits y conjuntos de variables.
