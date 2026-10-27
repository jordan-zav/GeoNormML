<p align="center"><strong>English</strong> · <a href="README.es.md">Español</a></p>

<div align="center">

# GeoNormML

[Work guide (Spanish)](docs/GUIA_DE_TRABAJO.md) · [Documentation index (Spanish)](docs/README.md) · [Script catalogue (Spanish)](scripts/README.md)

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
> [baseline correction](docs/revisiones/curated_baseline_correction_20260920.md) supersedes
> the earlier 2,651-row filtering experiment. Remove spatial join repetitions,
> preserve every curated sample ID and record additional checks as review warnings.

## Workflow at a glance

~~~text
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
~~~

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

## Data sources

Original datasets, intermediate tables and serialized trained models are not
distributed in this repository. Obtain source data from their providers and
retain query parameters, dates, source references and applicable terms.

- [GEOROC](https://georoc.eu): database-query compilations use CC BY-SA 4.0.
  Cite GEOROC and the original sample references; datasets in the separate
  GEOROC Data Repository may have provider-specific terms. Follow the
  [official citation and licensing guidance](https://georoc.eu/georoc/cite.asp).
- [INGEMMET / GEOCATMIN](https://geocatmin.ingemmet.gob.pe): consult the
  institutional lithogeochemical and geological data services, cite INGEMMET
  and check the terms of the specific dataset. This repository does not
  redistribute that database or grant rights to third-party data.

Place authorized files in the ignored local Dataset directory or configure
GEONORMML_DATASET_PATH. Regeneration is an explicit processing/training task,
not a side effect of installing this package or merging these branches.

## Installation

GeoNormML and GeoNormPy are sibling projects. Use an isolated Python 3.11
environment under the resource directory configured for your machine:

    python -m pip install -r requirements.txt
    python -m pip check
    python -m pytest -q

If this machine has DEVRESOURCES_RUN.cmd, run commands through that local
launcher to preserve workspace locks and session-specific temporary paths.
The launcher itself is not distributed. The [work guide](docs/GUIA_DE_TRABAJO.md)
lists the environment locations used on the PC and laptop; do not copy one
machine's path blindly to another.

The reusable package can then be imported as <code>geonormml</code>. Full pipeline runs
also require the private local datasets referenced by the project scripts.

<code>requirements.txt</code> installs this project and resolves GeoNormPy from
<code>../GeoNormPy</code>. <code>constraints-py311.txt</code> records the tested scientific dependencies.
Use the latest GeoNormPy checkout: its packaging needs setuptools 77 or newer
and an SPDX license expression without the obsolete license classifier.
For core ML development without CIPW calculation, install with
<code>python -m pip install -c constraints-py311.txt -e ".[dev]"</code>.

### Clean data and validate the baseline models

~~~powershell
python -m scripts.clean_dataset --input "<spatial v5.xlsx>" --reference "<curated v4.xlsx>"
python -m scripts.build_modeling_artifacts
python -m scripts.validate_models
python -m scripts.export_official_models
python -m scripts.generate_shap_plots
~~~

Cleaning creates <code>Dataset/Filtered/final/GeoNormML_training_curated.xlsx</code>, a CSV,
spatial-repeat audit, retained-review table and SHA-256 manifest. It checks the
reference workbook's IDs and original values before writing. By default no
curated sample is removed for duplicate chemistry, conflicting labels or CIPW
balance warnings. <code>--policy restricted_experiment</code> requires a separate output
and cannot be reused as the official pipeline input. Cleaning never overwrites its input or an
existing output. Set <code>GEONORMML_DATASET_PATH</code> to use another audited workbook;
set <code>GEONORMML_ARTIFACTS_DIR</code> to redirect generated artifacts. Export defaults
to the two geochemical baselines. <code>--include-spatial</code> adds experimental spatial
models, requiring separate geographic validation. Pipeline steps 8 and 9 now
export first, then explain those exact models with SHAP.

### Clean working copy

Keep source code, scientific documentation and conference materials in this
repository. Keep <code>Dataset/</code>, generated <code>artifacts/</code>, virtual environments,
caches, temporary reports and local credentials outside version control.
GeoNormPy remains a separate sibling repository. Existing local training
datasets and exports are not needed to build the Python package; they are
required to run the corresponding research stages.

## Pipeline entry points

| Script | Purpose |
| --- | --- |
| <code>scripts/run_pipeline.py</code> | Coordinate the main processing stages |
| <code>scripts/create_training_ready_dataset.py</code> | Build the modeling table |
| <code>scripts/run_ml_benchmark.py</code> | Compare candidate models |
| <code>scripts/export_official_models.py</code> | Export selected model artifacts |
| <code>scripts/generate_shap_plots.py</code> | Produce model-interpretation figures |
| <code>scripts/generate_reliability_dashboard.py</code> | Summarize reliability evidence |

Individual scripts expose the exact local file arguments and assumptions for
their stage. Review them before running against a new dataset.

## Scientific documentation

- [Dataset traceability](docs/metodologia/dataset_traceability.md)
- [Modeling pipeline](docs/metodologia/modeling_pipeline_bootstrap.md)
- [Implemented petrological features](docs/metodologia/implemented_petrological_features.md)
- [Spatial features and SHAP](docs/metodologia/implemented_spatial_features_and_shap.md)
- [Final model decision](docs/revisiones/feature_context_experiment_and_final_model_decision.md)

## Repository map

| Path | Contents |
| --- | --- |
| <code>src/geonormml</code> | Reusable data, feature, split and modeling modules |
| <code>scripts</code> | Preparation, modeling, evaluation and export commands |
| <code>docs/metodologia</code> | Dataset provenance, features and processing methodology |
| <code>docs/revisiones</code> | Baseline correction, audits and scientific decisions |
| <code>docs/informes</code> | Historical project reports |
| <code>docs/publicaciones</code> | Abstracts and manuscript drafts |
| <code>docs/*.jpg</code> | Existing source illustrations used by the poster builders |
| <code>poster_cpg23</code> | Conference-poster builders, configurations and previews |

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

## CIPW profile comparison and two-machine integration

The laptop contributes compare_cipw_profiles.py and report_cipw_profile_comparison.py.
The first performs an explicit research experiment with new estimator fits;
it is not a read-only validator and is not run on installation or merge.
The second checks saved predictions and renders the dated 26 October report.
It is not a generic report for arbitrary future experiments.

Both commands expose --help. The comparison requires an explicit GeoNormPy
source path and a new output directory; the report requires the completed
experiment directory. Local data, splits and trusted model bundles are
prerequisites and are not downloaded automatically.

    python -m scripts.compare_cipw_profiles --help
    python -m scripts.report_cipw_profile_comparison --help

See the [integration record](docs/revisiones/integracion_dos_pc_20261026.md).
No models were trained or replaced while integrating the branches.
