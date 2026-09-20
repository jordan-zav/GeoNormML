"""Explain the actual exported geochemical models, without fitting surrogate estimators."""

from __future__ import annotations

import hashlib
import json

import joblib
import matplotlib.pyplot as plt
import numpy as np
import shap

from geonormml.config import ARTIFACTS_DIR, RANDOM_STATE, ROCK_TYPE_COLUMN
from geonormml.data import load_training_dataset
from geonormml.provenance import training_provenance


def main() -> None:
    root = ARTIFACTS_DIR / "petropyqapf_transfer"
    schema = json.loads((root / "schemas/official_model_bundle.json").read_text(encoding="utf-8"))
    if schema["provenance"] != training_provenance():
        raise ValueError("Exported model provenance differs from the current dataset/environment.")
    output = ARTIFACTS_DIR / "shap_interpretation"
    output.mkdir(parents=True, exist_ok=True)
    df = load_training_dataset()
    records = []
    for spec in schema["official_models"]:
        path = root / spec["artifact_path"]
        bundle = joblib.load(path)
        domain = df[df[ROCK_TYPE_COLUMN].eq(spec["domain_code"])]
        sample = domain.sample(n=min(200, len(domain)), random_state=RANDOM_STATE)
        pipeline = bundle["estimator"]
        features = pipeline.named_steps["preprocessor"].transform(sample[bundle["feature_columns"]])
        estimator = pipeline.steps[-1][1]
        values = shap.TreeExplainer(estimator).shap_values(features)
        if isinstance(values, list):
            values = np.stack(values, axis=-1)
        values = np.asarray(values)
        importance = np.abs(values).mean(axis=(0, 2) if values.ndim == 3 else 0)
        columns = bundle["feature_columns"]
        if len(importance) != len(columns):
            raise ValueError("SHAP feature count differs from the exported schema.")
        indices = np.argsort(importance)[-20:]
        fig, ax = plt.subplots(figsize=(9, 7))
        ax.barh([columns[i] for i in indices], importance[indices])
        ax.set_xlabel("Mean absolute SHAP value")
        ax.set_title(f"{spec['domain_code']} / {spec['model_name']} / {spec['feature_set']}")
        fig.tight_layout()
        fig.savefig(output / f"{spec['domain_name']}_shap_bar.png", dpi=180)
        plt.close(fig)
        records.append(
            {
                "domain": spec["domain_code"],
                "model": spec["model_name"],
                "model_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "explanation_rows": len(sample),
                "feature_columns": columns,
                "mean_abs_shap": importance.tolist(),
            }
        )
    (output / "provenance.json").write_text(
        json.dumps(
            {"models": records, "scope": "Training-sample explanations of fitted models; not validation scores."},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
