"""Build a publication snapshot from verified local validation evidence.

No estimator is fitted, copied, loaded or overwritten. An existing snapshot is
never replaced. Dataset and model files remain outside the publication output.
"""

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

from geonormml.catalog import CURRENT_GENERATION, CURRENT_MODEL_SPECS, generation_catalog
from geonormml.config import ARTIFACTS_DIR, get_dataset_path
from geonormml.quality import CURATED_POLICY, sample_groups


def publication_snapshot(dataset, artifacts):
    dataset, artifacts = Path(dataset), Path(artifacts)
    digest = hashlib.sha256(dataset.read_bytes()).hexdigest()
    manifest = json.loads(dataset.with_suffix(".audit.json").read_text(encoding="utf-8"))
    validation = json.loads((artifacts / "validation/baseline_validation.json").read_text(encoding="utf-8"))
    if digest != manifest["output_sha256"] or digest != validation["provenance"]["dataset_sha256"]:
        raise ValueError("Dataset, audit and validation hashes must agree before publishing metrics.")
    if manifest.get("policy_id") != CURATED_POLICY:
        raise ValueError("Publication requires the preserved curated baseline, not a restricted experiment.")
    frame = pd.read_excel(dataset)
    if len(frame) != 2755 or not frame.ID_Final.is_unique:
        raise ValueError("This baseline requires all 2755 unique curated IDs.")
    predictions = pd.read_csv(artifacts / "validation/holdout_predictions.csv")
    split = json.loads((artifacts / "splits/holdout_split.json").read_text(encoding="utf-8"))
    train, test = set(split["train_ids"]), set(split["test_ids"])
    if (
        len(train) != len(split["train_ids"])
        or len(test) != len(split["test_ids"])
        or train & test
        or train | test != set(frame.ID_Final)
    ):
        raise ValueError("The reserved split must partition every curated ID without overlap or repetitions.")
    groups = pd.Series(sample_groups(frame).to_numpy(), index=frame.ID_Final)
    if set(groups.loc[list(train)]) & set(groups.loc[list(test)]):
        raise ValueError("Training and reserved data share sample groups.")
    if not predictions.ID_Final.is_unique or set(predictions.ID_Final) != set(split["test_ids"]):
        raise ValueError("Predictions must account for every reserved sample exactly once.")
    samples = frame.set_index("ID_Final")
    if not predictions.actual.eq(predictions.ID_Final.map(samples.ROCK_NAME)).all():
        raise ValueError("Prediction labels differ from the original dataset.")
    if not predictions.domain.eq(predictions.ID_Final.map(samples["ROCK TYPE"])).all():
        raise ValueError("Prediction domains differ from the original dataset.")
    models = []
    for spec in CURRENT_MODEL_SPECS:
        matches = [
            row
            for row in validation["models"]
            if row["domain"] == spec["domain_code"]
            and row["feature_set"] == spec["feature_set"]
            and row["model"] == spec["model_name"]
        ]
        if len(matches) != 1:
            raise ValueError("Exactly one matching validation record is required for each selected baseline.")
        row = matches[0]
        expected_train = frame.loc[frame.ID_Final.isin(train) & frame["ROCK TYPE"].eq(spec["domain_code"])]
        if row.get("validation") != "stratified_group_cv_training_partition" or row["n_rows"] != len(expected_train):
            raise ValueError("The CV metrics must refer to grouped validation of the training partition.")
        held = predictions.loc[predictions.domain == spec["domain_code"]]
        labels = sorted(frame.loc[frame["ROCK TYPE"] == spec["domain_code"], "ROCK_NAME"].unique())
        actual_metrics = {
            "accuracy": accuracy_score(held.actual, held.predicted),
            "f1_macro": f1_score(held.actual, held.predicted, labels=labels, average="macro", zero_division=0),
        }
        if len(held) != row["holdout_rows"] or any(
            abs(actual_metrics[key] - row["holdout_" + ("accuracy" if key == "accuracy" else "f1_macro")]) > 1e-12
            for key in actual_metrics
        ):
            raise ValueError("Saved validation metrics do not reproduce from holdout predictions.")
        models.append(
            {
                **spec,
                "training_rows": row["n_rows"],
                "holdout_rows": row["holdout_rows"],
                "cv": {key: row[key] for key in ("CA", "AUC_macro_ovr", "MCC", "F1_weighted", "F1_macro")},
                "holdout": actual_metrics,
            }
        )
    return {
        "generation_id": CURRENT_GENERATION,
        "dataset_sha256": digest,
        "rows": len(frame),
        "domain_counts": {key: int(value) for key, value in frame["ROCK TYPE"].value_counts().items()},
        "class_count": int(frame.ROCK_NAME.nunique()),
        "scope": "Grouped CV on training only; reserved holdout. No external spatial validation.",
        "models": models,
        "generation_catalog": generation_catalog(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=get_dataset_path())
    parser.add_argument("--artifacts", type=Path, default=ARTIFACTS_DIR)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    snapshot = publication_snapshot(args.dataset, args.artifacts)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(snapshot, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(f"Verified publication snapshot: {args.output}")


if __name__ == "__main__":
    main()
