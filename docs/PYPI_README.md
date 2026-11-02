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

After publication, installation will be:

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
