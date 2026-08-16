from __future__ import annotations

import json
import shutil
from pathlib import Path

import joblib
import pandas as pd
from sklearn.base import clone
from sklearn.preprocessing import LabelEncoder

from geonormml.config import ARTIFACTS_DIR, DATASET_PATH, DATASET_SHEET, ROCK_TYPE_COLUMN, TARGET_COLUMN, setup_logging
from geonormml.data import load_training_dataset
from geonormml.features import FEATURE_SETS
from geonormml.ml import build_models, build_preprocessor

logger = setup_logging("export_transfer_bundle_models")


TRANSFER_DIR = ARTIFACTS_DIR / "petropyqapf_transfer"
ALL_MODELS_DIR = TRANSFER_DIR / "all_models"
ALL_MODELS_MODELS_DIR = ALL_MODELS_DIR / "models"


PIPELINE_POLICIES = {
    "oxides_core": {
        "status": "official",
        "warning": "",
        "rationale": "Baseline geoquimico oficial y defendible.",
    },
    "cipw": {
        "status": "official",
        "warning": "",
        "rationale": "Pipeline oficial para evaluar mineralogia normativa por si sola.",
    },
    "combined_core": {
        "status": "official",
        "warning": "",
        "rationale": "Pipeline combinado oficial: oxidos confiables + CIPW.",
    },
    "oxides": {
        "status": "secondary",
        "warning": "Incluye CO2, F, Cl, SO3 y S, columnas con completitud muy baja o nula; no usar como baseline oficial.",
        "rationale": "Solo para comparacion extendida.",
    },
    "combined": {
        "status": "secondary",
        "warning": "Agrega variables raras de baja completitud al esquema combinado; no usar como baseline oficial.",
        "rationale": "Solo para comparacion extendida.",
    },
    "oxides_contextual": {
        "status": "experimental",
        "warning": "Incluye Clase_SiO2 y Serie_Mag, variables derivadas que pueden suavizar artificialmente el problema.",
        "rationale": "Experimento contextual, no recomendado para integracion oficial.",
    },
    "combined_contextual": {
        "status": "experimental",
        "warning": "Incluye Clase_SiO2 y Serie_Mag junto con CIPW; puede inflar artificialmente el desempeno.",
        "rationale": "Experimento contextual, no recomendado para integracion oficial.",
    },
    "combined_enriched": {
        "status": "official",
        "warning": "",
        "rationale": "Oxidos + CIPW + indices petrologicos derivados (ASI, Mg#, DI, ICN).",
    },
    "combined_enriched_spatial": {
        "status": "official",
        "warning": "Requiere coordenadas geográficas (LON, LAT) de la muestra.",
        "rationale": "Pipeline espacial oficial recomendado. 100% transferible y libre de target leakage (usa Trench_Dist y LAT). No requiere shapefiles pesados.",
    },
    "combined_enriched_geodata": {
        "status": "experimental",
        "warning": "Alto riesgo de Target Leakage por Geol_Unit (alta cardinalidad). No transferible fuera de Perú.",
        "rationale": "Pipeline experimental con geología regional (1:50k) e INGEMMET. Útil solo para análisis retrospectivo local.",
    },
    "combined_full": {
        "status": "experimental",
        "warning": "Incluye TODAS las features disponibles; riesgo de overfitting y dependencia de datos externos.",
        "rationale": "Pipeline exhaustivo para evaluacion, no recomendado para produccion.",
    },
}


def export_bundle(df: pd.DataFrame, domain_code: str, feature_set_name: str, model_name: str) -> dict[str, object]:
    domain_df = df[df[ROCK_TYPE_COLUMN] == domain_code].copy()
    feature_columns = FEATURE_SETS[feature_set_name].columns
    X = domain_df[feature_columns]
    y = domain_df[TARGET_COLUMN]

    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    preprocessor = build_preprocessor(feature_columns, domain_df)
    models = build_models(n_classes=len(label_encoder.classes_), preprocessor=preprocessor)
    estimator = clone(models[model_name])
    estimator.fit(X, y_encoded)

    domain_name = "volcanic" if domain_code == "VOL" else "plutonic"
    policy = PIPELINE_POLICIES[feature_set_name]

    bundle = {
        "domain_code": domain_code,
        "domain_name": domain_name,
        "feature_set": feature_set_name,
        "feature_columns": feature_columns,
        "model_name": model_name,
        "target_column": TARGET_COLUMN,
        "rock_type_column": ROCK_TYPE_COLUMN,
        "dataset_path": str(DATASET_PATH),
        "dataset_sheet": DATASET_SHEET,
        "n_rows": int(len(domain_df)),
        "n_classes": int(len(label_encoder.classes_)),
        "classes": label_encoder.classes_.tolist(),
        "label_encoder": label_encoder,
        "estimator": estimator,
        "transfer_status": policy["status"],
        "transfer_warning": policy["warning"],
        "transfer_rationale": policy["rationale"],
    }

    out_path = ALL_MODELS_MODELS_DIR / f"{domain_name}__{feature_set_name}__{model_name}.joblib"
    joblib.dump(bundle, out_path)

    return {
        "domain_code": domain_code,
        "domain_name": domain_name,
        "feature_set": feature_set_name,
        "model_name": model_name,
        "artifact_path": str(out_path),
        "status": policy["status"],
        "warning": policy["warning"],
        "rationale": policy["rationale"],
        "n_rows": int(len(domain_df)),
        "n_classes": int(len(label_encoder.classes_)),
        "classes": ", ".join(label_encoder.classes_.tolist()),
        "required_columns": ", ".join(feature_columns),
    }


def main() -> None:
    ALL_MODELS_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    metrics_df = pd.read_csv(ARTIFACTS_DIR / "ml_benchmark" / "metrics_summary.csv")
    df = load_training_dataset()

    exported_rows: list[dict[str, object]] = []
    for row in metrics_df.sort_values(["domain", "feature_set", "model"]).itertuples(index=False):
        exported = export_bundle(df, row.domain, row.feature_set, row.model)
        exported["CA"] = row.CA
        exported["AUC_macro_ovr"] = row.AUC_macro_ovr
        exported["MCC"] = row.MCC
        exported["F1_weighted"] = row.F1_weighted
        exported_rows.append(exported)

    export_df = pd.DataFrame(exported_rows)
    csv_path = ALL_MODELS_DIR / "all_models_catalog.csv"
    export_df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    json_path = ALL_MODELS_DIR / "all_models_catalog.json"
    json_path.write_text(
        json.dumps(
            {
                "dataset_path": str(DATASET_PATH),
                "dataset_sheet": DATASET_SHEET,
                "models": exported_rows,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    txt_path = ALL_MODELS_DIR / "all_models_catalog.txt"
    txt_path.write_text(export_df.to_string(index=False), encoding="utf-8")

    source_docs = [
        TRANSFER_DIR / "docs" / "feature_context_experiment_and_final_model_decision.md",
        TRANSFER_DIR / "docs" / "considerations_and_ml_architecture_review.md",
        TRANSFER_DIR / "docs" / "integration_spec.md",
        TRANSFER_DIR / "docs" / "model_logic_summary.md",
    ]
    docs_dir = ALL_MODELS_DIR / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    for source in source_docs:
        if source.exists():
            shutil.copy2(source, docs_dir / source.name)

    logger.info(csv_path)
    logger.info(json_path)
    logger.info(txt_path)
    logger.info(export_df[["domain_name", "feature_set", "model_name", "status", "artifact_path"]].to_string(index=False))


if __name__ == "__main__":
    main()
