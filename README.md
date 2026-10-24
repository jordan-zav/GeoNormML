<div align="center">

# GeoNormML

**Petrographically informed machine learning for whole-rock geochemistry**

Build traceable rock-classification experiments from cleaned geochemical data,
normative mineral features, spatial context and reproducible model evaluation.

[![Status: research](https://img.shields.io/badge/status-research-f59e0b)](#project-status)
[![Version 0.1.0](https://img.shields.io/badge/version-0.1.0-2563eb)](pyproject.toml)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![GeoNormPy](https://img.shields.io/badge/normative%20engine-GeoNormPy-0f766e)](https://github.com/jordan-zav/GeoNormPy)
[![License: GPL-3.0-or-later](https://img.shields.io/badge/license-GPL--3.0--or--later-0f766e)](LICENSE)

</div>

> [!IMPORTANT]
> GeoNormML is a research repository. The source datasets and trained model
> artifacts are intentionally excluded because they require separate provenance,
> permissions and storage. The repository alone is not a pretrained classifier.

> The official curated baseline contains **2,755 samples**. The
> [baseline correction](docs/curated_baseline_correction_20260920.md) supersedes
> the earlier 2,651-row filtering experiment. Remove spatial join repetitions,
> preserve every curated sample ID and record additional checks as review warnings.

## Workflow at a glance

```text
Whole-rock analyses + petrographic labels + coordinates
                         │
                         ▼
       Traceability review and quality filtering
                         │
                         ▼
        GeoNormPy CIPW features + spatial features
                         │
                         ▼
      Group-aware split ──► benchmark ──► final model
                         │
                         ▼
        SHAP diagnostics + figures + export bundle
```

## Capabilities

| Area | Included work |
| --- | --- |
| Data preparation | Name normalization, quality filters, stable IDs and training-ready tables |
| Petrological context | Rock-type harmonization and CIPW normative features generated with GeoNormPy |
| Spatial context | Spatial joins and contextual features for geographically aware experiments |
| Modeling | Scikit-learn and XGBoost benchmarks, evaluation and final-model export |
| Interpretation | Confusion matrices, SHAP summaries, TAS comparisons and reliability dashboards |
| Reproducibility | Scripted stages, documented feature decisions and transfer bundles |

## Inputs and outputs

### Expected inputs

- tabular whole-rock major-element analyses;
- petrographic or lithological labels with documented provenance;
- optional coordinates or GIS layers for spatial features; and
- an explicit project configuration and local data paths.

### Generated artifacts

- cleaned and training-ready tabular datasets;
- benchmark metrics and confusion matrices;
- SHAP and feature-importance figures;
- serialized model bundles; and
- technical and publication-ready figures.

Generated datasets and models must retain the lineage of their input records.
Spatial joins and CIPW values are derived features, not independent geological
observations.

## Fuentes de datos

Este repositorio **no incluye** las bases de datos originales, intermedias ni los modelos entrenados serializados, tanto por razones de almacenamiento y licencias como por trazabilidad de procedencia. Para reproducir los experimentos, los datos deben obtenerse directamente de sus fuentes primarias:

- **GEOROC** (*Geochemistry of Rocks of the Oceans and Continents*, DIGIS, Universidad de Göttingen): datos bajo la licencia [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Al utilizar datos de GEOROC es obligatorio citar a GEOROC y las referencias originales de cada muestra individual según [https://georoc.mpch-mainz.gwdg.de/georoc/cite.asp](https://georoc.mpch-mainz.gwdg.de/georoc/cite.asp), y cualquier conjunto derivado se distribuye bajo la licencia CC BY-SA 4.0.
  - *Obtención*: Descargar las consultas regionales o temáticas correspondientes (óxidos mayores de rocas ígneas) desde el portal oficial de [GEOROC](https://georoc.eu).
- **INGEMMET** (*Instituto Geológico, Minero y Metalúrgico del Perú*): Base de Datos Litogeoquímica del Perú, publicada a través del sistema de información geológica y catastral minera [GEOCATMIN](https://geocatmin.ingemmet.gob.pe). Datos de libre acceso; el presente repositorio no redistribuye la base y debe citarse explícitamente a INGEMMET como fuente institucional.
  - *Obtención*: Consultar y descargar las capas de litogeoquímica y geología a escala 1:100 000 mediante las herramientas de consulta y descarga de [GEOCATMIN](https://geocatmin.ingemmet.gob.pe).

Los datos y modelos entrenados no se incluyen en el repositorio; para utilizarlos, sitúe los archivos obtenidos en la carpeta local `Dataset/` (excluida del control de versiones) o apunte la variable de entorno `GEONORMML_DATASET_PATH` a su copia local, y ejecute el pipeline reproducible documentado a continuación para regenerar los modelos y artefactos.

## Installation

GeoNormML and GeoNormPy are sibling projects. Python 3.11 is the validated
environment. From the GeoNormML directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
python -m pytest -q
```

The reusable package can then be imported as `geonormml`. Full pipeline runs
also require the private local datasets referenced by the project scripts.

`requirements.txt` installs this project and resolves GeoNormPy from
`../GeoNormPy`. `constraints-py311.txt` records the tested scientific dependencies.
Use the latest GeoNormPy checkout: its packaging needs setuptools 77 or newer
and an SPDX license expression without the obsolete license classifier.
For core ML development without CIPW calculation, install with
`python -m pip install -c constraints-py311.txt -e ".[dev]"`.

### Clean data and validate the baseline models

```powershell
python -m scripts.clean_dataset --input "<spatial v5.xlsx>" --reference "<curated v4.xlsx>"
python -m scripts.build_modeling_artifacts
python -m scripts.validate_models
python -m scripts.export_official_models
python -m scripts.generate_shap_plots
```

Cleaning creates `Dataset/Filtered/final/GeoNormML_training_curated.xlsx`, a CSV,
spatial-repeat audit, retained-review table and SHA-256 manifest. It checks the
reference workbook's IDs and original values before writing. By default no
curated sample is removed for duplicate chemistry, conflicting labels or CIPW
balance warnings. `--policy restricted_experiment` requires a separate output
and cannot be reused as the official pipeline input. Cleaning never overwrites its input or an
existing output. Set `GEONORMML_DATASET_PATH` to use another audited workbook;
set `GEONORMML_ARTIFACTS_DIR` to redirect generated artifacts. Export defaults
to the two geochemical baselines. `--include-spatial` adds experimental spatial
models, requiring separate geographic validation. Pipeline steps 8 and 9 now
export first, then explain those exact models with SHAP.

### Clean working copy

Keep source code, scientific documentation and conference materials in this
repository. Keep `Dataset/`, generated `artifacts/`, virtual environments,
caches, temporary reports and local credentials outside version control.
GeoNormPy remains a separate sibling repository. Existing local training
datasets and exports are not needed to build the Python package; they are
required to run the corresponding research stages.

## Pipeline entry points

| Script | Purpose |
| --- | --- |
| `scripts/run_pipeline.py` | Coordinate the main processing stages |
| `scripts/create_training_ready_dataset.py` | Build the modeling table |
| `scripts/run_ml_benchmark.py` | Compare candidate models |
| `scripts/export_official_models.py` | Export selected model artifacts |
| `scripts/generate_shap_plots.py` | Produce model-interpretation figures |
| `scripts/generate_reliability_dashboard.py` | Summarize reliability evidence |

Individual scripts expose the exact local file arguments and assumptions for
their stage. Review them before running against a new dataset.

## Scientific documentation

- [Dataset traceability](docs/dataset_traceability.md)
- [Modeling pipeline](docs/modeling_pipeline_bootstrap.md)
- [Implemented petrological features](docs/implemented_petrological_features.md)
- [Spatial features and SHAP](docs/implemented_spatial_features_and_shap.md)
- [Final model decision](docs/feature_context_experiment_and_final_model_decision.md)

## Repository map

| Path | Contents |
| --- | --- |
| `src/geonormml` | Reusable data, feature, split and modeling modules |
| `scripts` | Preparation, modeling, evaluation and export commands |
| `docs` | Methodology, provenance reviews and project reports |
| `poster_cpg23` | Conference-poster builders, configurations and previews |

## Project status

Version 0.1.0 is an active research baseline. Model performance is meaningful
only for the documented dataset, label taxonomy and validation split; it must
not be generalized to new regions or sample populations without external
validation. The regression suite covers cleaning, spatial overlaps, sample-group
separation, exports, missing-data handling and estimator serialization. It does
not establish geological validity or geographic transferability.

## License

GeoNormML is distributed under the [GNU General Public License v3.0](LICENSE).

## Author and contact

Jordan Zavaleta — GisGeo Dev<br>
[jordanzav@gisgeo.dev](mailto:jordanzav@gisgeo.dev) · [gisgeo.dev](https://gisgeo.dev)
