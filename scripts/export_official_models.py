from __future__ import annotations

import argparse
import json
import shutil

import joblib
import pandas as pd
from sklearn.base import clone
from sklearn.preprocessing import LabelEncoder

from geonormml.catalog import CURRENT_GENERATION, CURRENT_MODEL_SPECS, generation_catalog
from geonormml.config import (
    ARTIFACTS_DIR,
    DATASET_SHEET,
    ROCK_TYPE_COLUMN,
    TARGET_COLUMN,
    get_dataset_path,
    setup_logging,
)
from geonormml.data import load_training_dataset
from geonormml.features import FEATURE_SETS
from geonormml.ml import build_models, build_preprocessor
from geonormml.provenance import training_provenance

logger = setup_logging("export_official_models")


MODELS_DIR = ARTIFACTS_DIR / "official_models"

OFFICIAL_MODEL_SPECS = [
    # Geochemical baselines; external applicability still requires validation.
    *(dict(spec) for spec in CURRENT_MODEL_SPECS),
    # Spatial experiments; no claim of geographic transferability.
    {
        "domain_code": "VOL",
        "domain_name": "volcanic",
        "feature_set": "combined_enriched_spatial",
        "model_name": "XGBoost",
        "model_type": "spatial_contextual",
    },
    {
        "domain_code": "PLU",
        "domain_name": "plutonic",
        "feature_set": "combined_enriched_spatial",
        "model_name": "XGBoost",
        "model_type": "spatial_contextual",
    },
]


def export_model(df: pd.DataFrame, spec: dict[str, str]) -> dict[str, object]:
    domain_df = df[df[ROCK_TYPE_COLUMN] == spec["domain_code"]].copy()
    feature_columns = FEATURE_SETS[spec["feature_set"]].columns
    X = domain_df[feature_columns]
    y = domain_df[TARGET_COLUMN]

    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    preprocessor = build_preprocessor(feature_columns, domain_df)
    models = build_models(n_classes=len(label_encoder.classes_), preprocessor=preprocessor)
    estimator = clone(models[spec["model_name"]])
    estimator.fit(X, y_encoded)

    bundle = {
        "domain_code": spec["domain_code"],
        "domain_name": spec["domain_name"],
        "feature_set": spec["feature_set"],
        "feature_columns": feature_columns,
        "model_name": spec["model_name"],
        "model_type": spec["model_type"],
        "target_column": TARGET_COLUMN,
        "rock_type_column": ROCK_TYPE_COLUMN,
        "dataset_path": get_dataset_path().name,
        "dataset_sheet": DATASET_SHEET,
        "n_rows": int(len(domain_df)),
        "n_classes": int(len(label_encoder.classes_)),
        "classes": label_encoder.classes_.tolist(),
        "label_encoder": label_encoder,
        "estimator": estimator,
        "provenance": training_provenance(),
        "transfer_status": "official" if spec["model_type"] == "geochemical_baseline" else "experimental",
        "generation_id": CURRENT_GENERATION if spec["model_type"] == "geochemical_baseline" else "spatial_experimental",
    }

    out_path = MODELS_DIR / f"{spec['domain_name']}__{spec['feature_set']}__{spec['model_name']}.joblib"
    joblib.dump(bundle, out_path)

    return {
        "domain": spec["domain_name"],
        "feature_set": spec["feature_set"],
        "model": spec["model_name"],
        "model_type": spec["model_type"],
        "n_rows": int(len(domain_df)),
        "n_classes": int(len(label_encoder.classes_)),
        "artifact_path": f"models/{out_path.name}",
        "required_columns": feature_columns,
        "classes": label_encoder.classes_.tolist(),
    }


def main(*, geochemical_only: bool = True) -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_training_dataset()
    specs = [s for s in OFFICIAL_MODEL_SPECS if not geochemical_only or s["model_type"] == "geochemical_baseline"]
    exported_rows = [export_model(df, spec) for spec in specs]

    manifest_df = pd.DataFrame(exported_rows)
    manifest_path = MODELS_DIR / "official_models_manifest.csv"
    manifest_df.to_csv(manifest_path, index=False, encoding="utf-8-sig")

    summary = {
        "dataset_path": get_dataset_path().name,
        "dataset_sheet": DATASET_SHEET,
        "provenance": training_provenance(),
        "exports": exported_rows,
    }
    summary_path = MODELS_DIR / "official_models_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    text_lines = [
        f"dataset_path: {get_dataset_path().name}",
        f"dataset_sheet: {DATASET_SHEET}",
        "",
        manifest_df.to_string(index=False),
    ]
    text_path = MODELS_DIR / "official_models_summary.txt"
    text_path.write_text("\n".join(text_lines), encoding="utf-8")

    transfer = ARTIFACTS_DIR / "petropyqapf_transfer"
    (transfer / "models").mkdir(parents=True, exist_ok=True)
    (transfer / "schemas").mkdir(parents=True, exist_ok=True)
    official = []
    for spec, row in zip(specs, exported_rows):
        filename = row["artifact_path"].split("/")[-1]
        shutil.copy2(MODELS_DIR / filename, transfer / "models" / filename)
        if spec["model_type"] == "geochemical_baseline":
            official.append(
                {
                    **spec,
                    "artifact_path": row["artifact_path"],
                    "required_columns": row["required_columns"],
                    "classes": row["classes"],
                }
            )
    manifest_df.to_csv(transfer / "models" / manifest_path.name, index=False, encoding="utf-8-sig")
    schema = {
        "project": "GeoNormML",
        "generation_id": CURRENT_GENERATION,
        "generation_catalog": generation_catalog(),
        "target_application": "PetroPyQAPF",
        "dataset": {"target_column": TARGET_COLUMN, "domain_column": ROCK_TYPE_COLUMN},
        "global_rules": {
            "separate_models_by_domain": True,
            "geospatial_predictors": "excluded",
            "do_not_use_as_predictors": [
                "Quality_Flag",
                "Quality_Flag_Recomputed",
                "ROCK_NAME",
                "Clase_SiO2",
                "Serie_Mag",
                "CO2",
                "F",
                "Cl",
                "SO3",
                "S",
                "Geol_Unit",
                "Metal_Belt",
                "UTM_Zone",
                "LON",
                "LAT",
                "Trench_Dist",
            ],
        },
        "feature_sets": {name: fs.columns for name, fs in FEATURE_SETS.items()},
        "official_models": official,
        "provenance": training_provenance(),
    }
    (transfer / "schemas" / "official_model_bundle.json").write_text(
        json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    logger.info(manifest_path)
    logger.info(summary_path)
    logger.info(text_path)
    logger.info(manifest_df.to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export geochemical baselines and optional spatial experiments.")
    parser.add_argument("--include-spatial", action="store_true")
    main(geochemical_only=not parser.parse_args().include_spatial)
