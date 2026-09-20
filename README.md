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

## Installation

GeoNormML and GeoNormPy are sibling projects. From the directory that contains
both repositories:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .\GeoNormPy
python -m pip install -e .\GeoNormML
```

The reusable package can then be imported as `geonormml`. Full pipeline runs
also require the private local datasets referenced by the project scripts.

When using `requirements.txt`, run `python -m pip install -r requirements.txt`
from the GeoNormML directory. It resolves GeoNormPy from `../GeoNormPy`, matching
the sibling layout above.

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
- [Academic traceability](docs/dataset_traceability_academic.md)
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
validation. An automated regression suite still needs to be defined before a
public software release.

## License

GeoNormML is distributed under the [GNU General Public License v3.0](LICENSE).

## Author and contact

Jordan Zavaleta — GisGeo Dev<br>
[jordanzav@gisgeo.dev](mailto:jordanzav@gisgeo.dev) · [gisgeo.dev](https://gisgeo.dev)
