# Installed application guide

[Español](USAGE.es.md) · [Publication procedure](PUBLISHING.md)

GeoNormML provides an installed command-line interface and Python prediction API.
It remains a prepared PyPI candidate. Install the verified wheel directly until
publication is explicitly authorized:

    python -m pip install /path/to/geonormml-0.1.0-py3-none-any.whl
    geonormml --version
    geonormml --help

If an earlier unreleased 0.1.0 candidate is already installed, use pip install
--force-reinstall with the new wheel so the previous candidate is replaced.

The dependency GeoNormPy 1.1.0 is resolved from PyPI. No private data or weights
are downloaded. Python 3.11 is the validated environment. A model's recorded
scientific-library versions must also match before it can be loaded.

## Start with the runnable synthetic example

Use a new directory, including spaces if desired:

    geonormml example --output "/my/work/model example"
    geonormml inspect "/my/work/model example/manifest.json"
    geonormml predict --model "/my/work/model example/manifest.json" --input "/my/work/model example/input.csv" --output "/my/work/predictions.csv" --id-column Sample_ID --trust-model

The example generates invented chemistry, arbitrary Synthetic_A / Synthetic_B
labels and a DummyClassifier. It exercises real CIPW features and inference
plumbing, not geological accuracy. It creates only the requested new directory.
Repeating a command with an existing destination fails rather than overwriting it.

Every successful command emits one JSON object on stdout. Diagnostics go to
stderr. Errors return code 2 and a structured error object on stderr. The same
commands are available through python -m geonormml.

## Portable paths

    geonormml paths

This reports paths without creating directories. An installed wheel uses a
user-owned application directory: LOCALAPPDATA/geonormml on Windows,
~/Library/Application Support/geonormml on macOS, and
XDG_DATA_HOME/geonormml or ~/.local/share/geonormml on Linux.

| Setting | Purpose |
| --- | --- |
| GEONORMML_HOME | Override the user-owned application directory |
| GEONORMML_MODELS_DIR | Override the model-manifest registry |
| GEONORMML_ARTIFACTS_DIR | Override research artifact outputs |
| GEONORMML_DATASET_PATH | Explicit research training workbook; inference does not read it |
| GEONORMML_PROJECT_ROOT | Explicit research checkout/root, preserving its Dataset/Filtered/final layout |

Paths are expanded and resolved. A real src checkout is detected for historical
research-script compatibility; an installed wheel does not infer its project
root from site-packages. In a checkout, research artifacts retain that project's
artifacts directory unless explicitly overridden. The portable model registry
uses the user directory regardless. Inspect paths before research scripts run.
No inference command reads a training dataset or initiates research training.

For the development PC, use its D:/DevResources resource folders and existing
local launchers. Keep source code and source extractions under O:/0. Projects.

## Model registry and inspection

Put an authorized bundle in a directory of your choice:

    models/
      my-volcanic-model/
        manifest.json
        model.joblib

Point GEONORMML_MODELS_DIR to models, then:

    geonormml models
    geonormml inspect my-volcanic-model

You can always use an explicit manifest path instead of the registry. Listing
reads JSON only. Inspection verifies recorded versions and SHA-256 without
deserializing the model; --metadata-only skips those byte/environment checks.
A hash proves byte agreement with a manifest, not trust in the publisher.

Loading joblib can execute code. Load only models from a source you trust, using
trusted=True in Python or --trust-model in the CLI. See the official
[scikit-learn persistence guidance](https://scikit-learn.org/stable/model_persistence.html).
The loader does not silently install dependencies or downgrade the environment.

## Attach an existing model's known contract

Existing project exports are dictionaries with estimator, classes or
label_encoder, feature_columns, generation_id and optionally domain_code.
The adapter also understands feature columns recorded in selected.columns.
It does not infer a training contract from a filename or a current environment.

For an authorized historical artifact, prepare a JSON metadata document with:

- generation_id, domain_code (VOL or PLU), ordered feature_columns and ordered
  class labels from the saved training record;
- input_mode prepared_features and prediction_encoding encoded or labels;
- categorical_columns when prepared inputs contain category strings;
- python_version in major.minor form and exact dependencies for scikit-learn,
  numpy, scipy and joblib, plus xgboost or other required estimator libraries;
- no normative recomputation contract for prepared_features.

Then attach the manifest without loading or modifying the model:

    geonormml manifest --model-file "/my/model/model.joblib" --metadata "/my/model/recorded-contract.json"

This writes a new manifest.json alongside the artifact and adds its SHA-256.
Existing files are preserved. create_model_manifest provides the same operation
in Python. runtime_dependencies() is a convenience for a newly serialized model
in its actual training environment, not a way to guess an older model's versions.

## Input modes

prepared_features consumes the exact declared columns in their training order.
It does not recompute CIPW or derived features. Record category columns explicitly;
numeric measurements are parsed and missing values are left for the trained
preprocessor. This is the compatible route for legacy bundles whose original
normative provenance was not recorded completely.
Experimental models with spatial variables require already prepared columns;
their geographic and scientific transfer limits remain in force.

oxide_chemistry currently supports oxides_core, combined_core,
combined_contextual and combined_enriched. Raw chemistry requires ten measured
major inputs: SiO2, TiO2, Al2O3, FeOT, CaO, MgO, MnO, Na2O, K2O and P2O5,
in weight percent. Missing LOI and Sum_Oxs stay missing; measured negative LOI is
preserved. Analytical totals are not recomputed. Optional normative inputs are
CO2, F, Cl, SO3, S, ZrO2 and Cr2O3. Old norm/category columns are ignored and
recomputed rather than reused. The chemistry adapter does not derive or supply
spatial predictors.

For normative features the manifest must explicitly record:

    "normative": {
      "engine_version": "1.1.0",
      "profile": "verma2003",
      "profile_version": "1.0",
      "iron_policy": "fixed",
      "fe3_fraction": 0.15,
      "carbonate_mode": "calcite",
      "apatite_feature": "Ap + FAp"
    }

The compatibility and Pruseth profiles are also selectable with their recorded
profile versions. The installed chemistry adapter currently implements fixed
FeOT partitioning and the calcite convention; other iron/carbonate contracts
must use prepared_features until explicitly implemented and verified.

Raw-chemistry artifacts must themselves contain the same input_mode,
feature_set and normative contract, in addition to their estimator metadata.
Changing only a JSON manifest cannot change the contract stored in the artifact.
Old v2/v5 research exports that lack that complete contract remain usable with
prepared_features. An owner can create a separate, verified adapter bundle from
recorded training provenance; the library never rewrites a historical binary or
promotes it to another generation automatically.

## Python API

    import pandas as pd
    from geonormml import inspect_model, load_model, predict

    info = inspect_model("/my/model/manifest.json")
    model = load_model("/my/model/manifest.json", trusted=True)
    samples = pd.read_csv("/my/input.csv", dtype={"Sample_ID": str})
    result = predict(samples, model, id_column="Sample_ID")
    print(result[["sample_id", "prediction", "status", "error_code"]])

The input frame is preserved. Output retains every row and original Python
index, including repeated indices; input_row is its positional identity.
CSV input preserves lexical IDs such as 001 and NA. Blank numeric fields mean
missing measurements, not zero. When ROCK TYPE is supplied, rows outside the
selected model's domain are rejected. Without it, selecting a model is the
explicit domain choice; there is no automatic VOL/PLU routing.

## Rejections and output

| Error/status | Meaning |
| --- | --- |
| missing_columns | Required headers are absent; the request fails before writing output |
| invalid_numeric_input | A row contains a nonnumeric, infinite or boolean numeric measurement |
| missing_major | A raw-chemistry row lacks a required measured major |
| negative_oxide | A supplied oxide/component is negative; LOI is treated separately |
| domain_mismatch | The row's ROCK TYPE does not match the selected model |
| incomplete_norm / normative_error | The calculation cannot supply a complete supported norm |
| checksum_mismatch / environment_mismatch | The model is not loaded |
| bundle_mismatch | Artifact columns, classes, generation or raw-input contract disagree |

Rejected rows have no predicted label or class probabilities. Valid rows continue.
The output includes probability::<class> only as the model's probability; if the
estimator has no probability method, those values remain missing. They are not
certified confidence or externally demonstrated calibration. Batch-level model
failures return an error rather than writing a partial prediction file.

The CLI reads a CSV into memory and writes a new result file only. It preserves
the input, selected model and any existing output. This workflow does not supply
an external evaluation, petrographic certification or a claim of regional transfer.
