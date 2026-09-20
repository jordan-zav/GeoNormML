"""Evaluate the two fixed geochemical baselines with grouped CV and a reserved holdout."""

import json

import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import LabelEncoder

from geonormml.config import ARTIFACTS_DIR, ID_COLUMN, ROCK_TYPE_COLUMN, TARGET_COLUMN
from geonormml.data import load_training_dataset
from geonormml.features import FEATURE_SETS
from geonormml.ml import build_models, build_preprocessor
from geonormml.provenance import training_provenance
from geonormml.split import make_holdout_split
from scripts import run_ml_benchmark as benchmark
from scripts.export_official_models import OFFICIAL_MODEL_SPECS


def main():
    root = ARTIFACTS_DIR / "validation"
    benchmark.CONFUSION_DIR = root / "confusion_matrices"
    benchmark.ROC_DIR = root / "roc_curves"
    benchmark.CONFUSION_DIR.mkdir(parents=True, exist_ok=True)
    benchmark.ROC_DIR.mkdir(parents=True, exist_ok=True)
    df = load_training_dataset()
    split = make_holdout_split(df, ID_COLUMN)
    rows = []
    predictions = []
    for spec in OFFICIAL_MODEL_SPECS:
        if spec["model_type"] != "geochemical_baseline":
            continue
        domain = df[df[ROCK_TYPE_COLUMN].eq(spec["domain_code"])]
        train = domain[domain[ID_COLUMN].isin(split.train_ids)]
        test = domain[domain[ID_COLUMN].isin(split.test_ids)]
        columns = FEATURE_SETS[spec["feature_set"]].columns
        encoder = LabelEncoder().fit(train[TARGET_COLUMN])
        model = build_models(len(encoder.classes_), build_preprocessor(columns, train))[spec["model_name"]]
        metrics = benchmark.evaluate_combo(train, spec["domain_code"], spec["feature_set"], spec["model_name"], model)
        model.fit(train[columns], encoder.transform(train[TARGET_COLUMN]))
        predicted = encoder.inverse_transform(model.predict(test[columns]))
        metrics.update(
            {
                "holdout_rows": len(test),
                "holdout_accuracy": accuracy_score(test[TARGET_COLUMN], predicted),
                "holdout_f1_macro": f1_score(test[TARGET_COLUMN], predicted, average="macro", zero_division=0),
            }
        )
        rows.append(metrics)
        predictions.extend(
            {"ID_Final": int(sample_id), "domain": spec["domain_code"], "actual": actual, "predicted": prediction}
            for sample_id, actual, prediction in zip(test[ID_COLUMN], test[TARGET_COLUMN], predicted)
        )
        print(
            f"{spec['domain_code']} / {spec['model_name']}: CV={metrics['CA']:.4f}, "
            f"holdout={metrics['holdout_accuracy']:.4f}",
            flush=True,
        )
    result = {
        "provenance": training_provenance(),
        "models": rows,
        "scope": "Fixed baseline models; sample-group validation, not spatial or external validation.",
    }
    (root / "baseline_validation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(predictions).to_csv(root / "holdout_predictions.csv", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
