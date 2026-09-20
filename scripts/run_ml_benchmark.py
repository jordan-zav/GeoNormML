from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.base import clone
from sklearn.metrics import (
    accuracy_score,
    auc,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.preprocessing import LabelEncoder, label_binarize

from geonormml.config import ARTIFACTS_DIR, ID_COLUMN, ROCK_TYPE_COLUMN, TARGET_COLUMN, setup_logging
from geonormml.data import load_training_dataset
from geonormml.features import FEATURE_SETS
from geonormml.ml import build_models, build_preprocessor
from geonormml.provenance import training_provenance
from geonormml.split import grouped_cv_indices, make_holdout_split

logger = setup_logging("run_ml_benchmark")


RESULTS_DIR = ARTIFACTS_DIR / "ml_benchmark"
CONFUSION_DIR = RESULTS_DIR / "confusion_matrices"
ROC_DIR = RESULTS_DIR / "roc_curves"

DOMAINS = {
    "VOL": "Rocas volcánicas",
    "PLU": "Rocas plutónicas",
}

FEATURE_SET_NAMES = [
    "oxides_core",
    "oxides",
    "cipw",
    "combined_core",
    "combined",
    "oxides_contextual",
    "combined_contextual",
    "combined_enriched",
    "combined_enriched_spatial",
    # Geodata sets — auto-skipped if spatial join hasn't been run
    "combined_enriched_geodata",
    "combined_full",
]


def compute_multiclass_roc(
    y_true_encoded: np.ndarray, y_prob: np.ndarray, class_names: list[str]
) -> tuple[float, dict]:
    y_bin = label_binarize(y_true_encoded, classes=np.arange(len(class_names)))
    if len(class_names) == 2:
        y_bin = np.column_stack([1 - y_bin[:, 0], y_bin[:, 0]])
    auc_macro = roc_auc_score(y_bin, y_prob, multi_class="ovr", average="macro")

    per_class = {}
    for idx, class_name in enumerate(class_names):
        fpr, tpr, _ = roc_curve(y_bin[:, idx], y_prob[:, idx])
        per_class[class_name] = {
            "fpr": fpr.tolist(),
            "tpr": tpr.tolist(),
            "auc": float(auc(fpr, tpr)),
        }

    all_fpr = np.unique(np.concatenate([np.array(per_class[name]["fpr"]) for name in class_names]))
    mean_tpr = np.zeros_like(all_fpr)
    for name in class_names:
        mean_tpr += np.interp(all_fpr, np.array(per_class[name]["fpr"]), np.array(per_class[name]["tpr"]))
    mean_tpr /= len(class_names)
    macro_auc_curve = auc(all_fpr, mean_tpr)

    roc_payload = {
        "macro_curve": {
            "fpr": all_fpr.tolist(),
            "tpr": mean_tpr.tolist(),
            "auc": float(macro_auc_curve),
        },
        "per_class": per_class,
    }
    return float(auc_macro), roc_payload


def plot_confusion(cm: np.ndarray, labels: list[str], title: str, out_path: Path) -> None:
    plt.figure(figsize=(max(8, len(labels) * 0.8), max(6, len(labels) * 0.7)))
    sns.heatmap(cm, annot=True, fmt="d", cmap="YlGnBu", xticklabels=labels, yticklabels=labels)
    plt.title(title)
    plt.xlabel("Clase predicha")
    plt.ylabel("Clase real")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def plot_macro_roc(roc_payload: dict, title: str, out_path: Path) -> None:
    macro = roc_payload["macro_curve"]
    plt.figure(figsize=(7, 6))
    plt.plot(macro["fpr"], macro["tpr"], label=f"ROC macro (AUC={macro['auc']:.3f})", color="#2c7fb8")
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray")
    plt.xlabel("Tasa de falsos positivos")
    plt.ylabel("Tasa de verdaderos positivos")
    plt.title(title)
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def evaluate_combo(df: pd.DataFrame, domain_code: str, feature_set_name: str, model_name: str, model) -> dict:
    feature_columns = FEATURE_SETS[feature_set_name].columns
    X = df[feature_columns]
    y = df[TARGET_COLUMN]

    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    class_names = label_encoder.classes_.tolist()

    cv = grouped_cv_indices(df)
    y_pred_encoded = np.empty(len(df), dtype=int)
    y_prob = np.empty((len(df), len(class_names)))
    for train, valid in cv:
        estimator = clone(model).fit(X.iloc[train], y_encoded[train])
        y_pred_encoded[valid] = estimator.predict(X.iloc[valid])
        y_prob[valid] = estimator.predict_proba(X.iloc[valid])

    cm = confusion_matrix(y_encoded, y_pred_encoded)
    auc_macro_ovr, roc_payload = compute_multiclass_roc(y_encoded, y_prob, class_names)

    metrics = {
        "domain": domain_code,
        "feature_set": feature_set_name,
        "model": model_name,
        "n_rows": len(df),
        "n_classes": len(class_names),
        "validation": "stratified_group_cv_training_partition",
        "CA": float(accuracy_score(y_encoded, y_pred_encoded)),
        "AUC_macro_ovr": float(auc_macro_ovr),
        "F1_weighted": float(f1_score(y_encoded, y_pred_encoded, average="weighted", zero_division=0)),
        "Precision_weighted": float(precision_score(y_encoded, y_pred_encoded, average="weighted", zero_division=0)),
        "Recall_weighted": float(recall_score(y_encoded, y_pred_encoded, average="weighted", zero_division=0)),
        "MCC": float(matthews_corrcoef(y_encoded, y_pred_encoded)),
        "F1_macro": float(f1_score(y_encoded, y_pred_encoded, average="macro", zero_division=0)),
        "Precision_macro": float(precision_score(y_encoded, y_pred_encoded, average="macro", zero_division=0)),
        "Recall_macro": float(recall_score(y_encoded, y_pred_encoded, average="macro", zero_division=0)),
    }

    domain_name = DOMAINS[domain_code]
    file_domain = {"VOL": "volcanic", "PLU": "plutonic"}[domain_code]
    stem = f"{file_domain}__{feature_set_name}__{model_name}"

    cm_csv = CONFUSION_DIR / f"{stem}.csv"
    pd.DataFrame(cm, index=class_names, columns=class_names).to_csv(cm_csv, encoding="utf-8-sig")
    plot_confusion(cm, class_names, f"{domain_name} | {feature_set_name} | {model_name}", CONFUSION_DIR / f"{stem}.png")

    roc_json = ROC_DIR / f"{stem}.json"
    roc_json.write_text(json.dumps(roc_payload, indent=2), encoding="utf-8")
    plot_macro_roc(roc_payload, f"{domain_name} | {feature_set_name} | {model_name}", ROC_DIR / f"{stem}.png")

    return metrics


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    CONFUSION_DIR.mkdir(parents=True, exist_ok=True)
    ROC_DIR.mkdir(parents=True, exist_ok=True)

    df = load_training_dataset()
    holdout = make_holdout_split(df, id_column=ID_COLUMN)
    df = df[df[ID_COLUMN].isin(holdout.train_ids)].copy()

    all_metrics: list[dict] = []
    for domain_code in ["VOL", "PLU"]:
        domain_df = df[df[ROCK_TYPE_COLUMN] == domain_code].copy()

        for feature_set_name in FEATURE_SET_NAMES:
            feature_cols = FEATURE_SETS[feature_set_name].columns
            missing_cols = [c for c in feature_cols if c not in domain_df.columns]
            if missing_cols:
                logger.warning(
                    "Skipping %s | %s — missing columns: %s",
                    domain_code,
                    feature_set_name,
                    missing_cols,
                )
                continue

            preprocessor = build_preprocessor(feature_cols, domain_df)
            models = build_models(
                n_classes=domain_df[TARGET_COLUMN].nunique(),
                preprocessor=preprocessor,
            )
            for model_name, model in models.items():
                logger.info(f"Running {domain_code} | {feature_set_name} | {model_name}")
                metrics = evaluate_combo(domain_df, domain_code, feature_set_name, model_name, model)
                all_metrics.append(metrics)

    metrics_df = pd.DataFrame(all_metrics).sort_values(["domain", "feature_set", "model"])
    metrics_path = RESULTS_DIR / "metrics_summary.csv"
    metrics_df.to_csv(metrics_path, index=False, encoding="utf-8-sig")
    (RESULTS_DIR / "provenance.json").write_text(json.dumps(training_provenance(), indent=2) + "\n", encoding="utf-8")

    summary_path = RESULTS_DIR / "metrics_summary.txt"
    summary_path.write_text(metrics_df.to_string(index=False), encoding="utf-8")

    logger.info(metrics_path)
    logger.info(summary_path)
    logger.info(metrics_df.to_string(index=False))


if __name__ == "__main__":
    main()
