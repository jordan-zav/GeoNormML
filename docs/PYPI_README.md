# GeoNormML

Research utilities for petrographically informed machine learning with whole-rock
geochemistry. GeoNormML provides data validation, feature preparation, grouped
evaluation and model-export helpers. GeoNormPy 1.1.0 is installed as an exact,
separate dependency for normative CIPW calculations.

## Scope

This package distributes source code. It does not include a training dataset,
pretrained classifier, application installer or private model weights. Installing
it does not train a model or download those resources. PetroPyQAPF's operational
v5 adoption is a separate application integration.

Installation:

    python -m pip install geonormml==0.1.0

Python 3.10 or newer is declared; the validated scientific environment uses
Python 3.11. See the repository constraints file for that development environment.

## Inspect package and model-contract metadata

    import geonormml
    from geonormml.catalog import generation_catalog

    print(geonormml.__version__)
    contract = generation_catalog(include_operational=True)
    print(contract["operational_adoption"]["generation_id"])

This example reads metadata only. Historical export identities remain unchanged.
For source-only research scripts, use the source distribution or repository and
explicitly provide authorized input data and new output paths.

## Installed command and prediction API

The wheel installs the geonormml command. Its portable defaults use user-owned
storage; data and artifacts never default to the Python installation directory.

    geonormml paths
    geonormml example --output "/my/work/new synthetic example"
    geonormml inspect "/my/work/new synthetic example/manifest.json"
    geonormml predict --model "/my/work/new synthetic example/manifest.json" --input "/my/work/new synthetic example/input.csv" --output "/my/work/predictions.csv" --id-column Sample_ID --trust-model

The example generates invented chemistry and a DummyClassifier with arbitrary
labels, not a geologically validated model. Existing outputs are preserved.
For your own model, provide an explicit manifest recording its feature order,
classes, domain, training-library versions and input contract. Inspection reads
metadata and hashes without deserializing model objects. Loading joblib requires
an explicitly trusted source.

    import pandas as pd
    from geonormml import load_model, predict
    model = load_model("/my/work/new synthetic example/manifest.json", trusted=True)
    samples = pd.read_csv("/my/work/new synthetic example/input.csv", dtype={"Sample_ID": str})
    results = predict(samples, model, id_column="Sample_ID")

Raw chemistry uses a declared, checked normative contract; historical models can
consume prepared features without silently changing their CIPW profile. Every
input row is retained, with explicit rejections and missing predictions where
appropriate. No dataset or scientific model is selected automatically.

See the [application guide](https://github.com/jordan-zav/GeoNormML/blob/main/docs/USAGE.md)
for path configuration, metadata registration, supported chemistry and output fields.

## Scientific limits

A CIPW norm is not measured modal mineralogy. Internal grouped validation does
not establish external accuracy or geographic transfer. Model probabilities do
not have externally demonstrated calibration. Plutonic predictions have important
class-level limitations and remain supporting information.

- [Current state and pending work](https://github.com/jordan-zav/GeoNormML/blob/main/docs/STATUS.md).
- [Spanish documentation](https://github.com/jordan-zav/GeoNormML/blob/main/README.es.md).
- [External evaluation plan](https://github.com/jordan-zav/GeoNormML/blob/main/docs/EXTERNAL_VALIDATION.md).
- [Source and issue tracker](https://github.com/jordan-zav/GeoNormML).

GPL-3.0-or-later. Author: Jordan Zavaleta.
