from __future__ import annotations

import json

import joblib
import pandas as pd
from sklearn.base import clone
from sklearn.preprocessing import LabelEncoder

from geonormml.config import ARTIFACTS_DIR, DATASET_PATH, DATASET_SHEET, ROCK_TYPE_COLUMN, TARGET_COLUMN, setup_logging
from geonormml.data import load_training_dataset
from geonormml.features import FEATURE_SETS
from geonormml.ml import build_models, build_preprocessor

logger = setup_logging("export_official_models")


MODELS_DIR = ARTIFACTS_DIR / "official_models"

OFFICIAL_MODEL_SPECS = [
    # --- Geochemical Baseline Models (Universal, pure chemistry) ---
    {
        "domain_code": "VOL",
        "domain_name": "volcanic",
        "feature_set": "combined_core",
        "model_name": "XGBoost",
        "model_type": "geochemical_baseline",
    },
    {
        "domain_code": "PLU",
        "domain_name": "plutonic",
        "feature_set": "combined_core",  # Changed from oxides_core to combined_core for mineralogical consistency (CIPW)
        "model_name": "RandomForest",
        "model_type": "geochemical_baseline",
    },
    # --- Spatial-Contextual Models (Recommended for Peru/Andes, 100% transferrable, no leakage) ---
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
        "dataset_path": str(DATASET_PATH),
        "dataset_sheet": DATASET_SHEET,
        "n_rows": int(len(domain_df)),
        "n_classes": int(len(label_encoder.classes_)),
        "classes": label_encoder.classes_.tolist(),
        "label_encoder": label_encoder,
        "estimator": estimator,
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
        "artifact_path": str(out_path),
    }


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_training_dataset()
    exported_rows = [export_model(df, spec) for spec in OFFICIAL_MODEL_SPECS]

    manifest_df = pd.DataFrame(exported_rows)
    manifest_path = MODELS_DIR / "official_models_manifest.csv"
    manifest_df.to_csv(manifest_path, index=False, encoding="utf-8-sig")

    summary = {
        "dataset_path": str(DATASET_PATH),
        "dataset_sheet": DATASET_SHEET,
        "exports": exported_rows,
    }
    summary_path = MODELS_DIR / "official_models_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    text_lines = [
        f"dataset_path: {DATASET_PATH}",
        f"dataset_sheet: {DATASET_SHEET}",
        "",
        manifest_df.to_string(index=False),
    ]
    text_path = MODELS_DIR / "official_models_summary.txt"
    text_path.write_text("\n".join(text_lines), encoding="utf-8")

    logger.info(manifest_path)
    logger.info(summary_path)
    logger.info(text_path)
    logger.info(manifest_df.to_string(index=False))


if __name__ == "__main__":
    main()
