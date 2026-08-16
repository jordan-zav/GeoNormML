# GeoNormML

Machine-learning pipeline for petrographic rock classification using geochemical and spatial data.

## Repository scope

This repository contains the reusable Python package, pipeline scripts, project documentation, and publication assets. Large source datasets and generated model artifacts are intentionally excluded from Git.

## Layout

- `src/geonormml`: reusable package code
- `scripts`: data preparation, modeling, evaluation, and export commands
- `docs`: methodology, traceability, and project reports
- `poster_cpg23`: conference poster source and assets

## Installation

```bash
python -m pip install -e .
```

The local `Dataset` and `artifacts` directories are required for full pipeline runs but are not distributed in this repository.
