"""Controlled diagnostic of CV population, sample grouping and feature selection.

Fits temporary estimators only. Uses the same stored chemistry/norms throughout;
does not recalculate CIPW, serialize models or update the production artifacts.
The full-population scenarios deliberately reuse the old holdout for diagnosis,
so their scores must never be described as a new independent evaluation.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import accuracy_score, f1_score, matthews_corrcoef
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder

from geonormml.config import ARTIFACTS_DIR, RANDOM_STATE, get_dataset_path
from geonormml.data import load_training_dataset
from geonormml.features import FEATURE_SETS
from geonormml.ml import build_models, build_preprocessor
from geonormml.quality import sample_groups
from geonormml.split import grouped_cv_indices


def diagnostic_folds(frame, grouped):
    if grouped:
        return grouped_cv_indices(frame)
    return list(StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE).split(frame, frame.ROCK_NAME))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    originals = {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest()
        for folder in (get_dataset_path().parents[2], ARTIFACTS_DIR)
        for path in folder.rglob("*")
        if path.is_file()
    }
    frame = load_training_dataset()
    split = json.loads((ARTIFACTS_DIR / "splits/holdout_split.json").read_text(encoding="utf-8"))
    validation = json.loads((ARTIFACTS_DIR / "validation/baseline_validation.json").read_text(encoding="utf-8"))
    records, predictions = [], []
    for domain, feature_set, model_name in (
        ("VOL", "combined_core", "XGBoost"),
        ("PLU", "combined_core", "RandomForest"),
        ("PLU", "oxides_core", "RandomForest"),
    ):
        for population in ("recorded_training", "all_curated_diagnostic"):
            subset = frame.loc[frame["ROCK TYPE"].eq(domain)]
            if population == "recorded_training":
                subset = subset.loc[subset.ID_Final.isin(split["train_ids"])]
            subset = subset.reset_index(drop=True)
            columns = FEATURE_SETS[feature_set].columns
            encoder = LabelEncoder().fit(subset.ROCK_NAME)
            target = encoder.transform(subset.ROCK_NAME)
            template = build_models(len(encoder.classes_), build_preprocessor(columns, subset))[model_name]
            groups = sample_groups(subset)
            for grouped in (False, True):
                predicted = np.full(len(subset), -1, dtype=int)
                overlap_groups, fold_membership = [], np.zeros(len(subset), dtype=int)
                for fold_number, (train, valid) in enumerate(diagnostic_folds(subset, grouped), start=1):
                    overlaps = set(groups.iloc[train]) & set(groups.iloc[valid])
                    if grouped and overlaps:
                        raise AssertionError("Grouped evaluation leaks sample groups")
                    overlap_groups.append(len(overlaps))
                    estimator = clone(template).fit(subset.iloc[train][columns], target[train])
                    predicted[valid] = estimator.predict(subset.iloc[valid][columns])
                    fold_membership[valid] += 1
                    predictions.extend(
                        {
                            "ID_Final": int(subset.iloc[index].ID_Final),
                            "domain": domain,
                            "feature_set": feature_set,
                            "population": population,
                            "grouped": grouped,
                            "fold": fold_number,
                            "actual": str(subset.iloc[index].ROCK_NAME),
                            "predicted": str(encoder.classes_[predicted[index]]),
                        }
                        for index in valid
                    )
                if not (fold_membership == 1).all() or (predicted < 0).any():
                    raise AssertionError("Every diagnostic sample must have exactly one OOF prediction")
                item = {
                    "domain": domain,
                    "feature_set": feature_set,
                    "model": model_name,
                    "population": population,
                    "grouped": grouped,
                    "rows": len(subset),
                    "accuracy": float(accuracy_score(target, predicted)),
                    "f1_macro": float(f1_score(target, predicted, average="macro", zero_division=0)),
                    "mcc": float(matthews_corrcoef(target, predicted)),
                    "overlapping_groups_per_fold": overlap_groups,
                }
                if population == "recorded_training" and grouped and feature_set == "combined_core":
                    expected = next(row for row in validation["models"] if row["domain"] == domain)
                    if abs(item["accuracy"] - expected["CA"]) > 1e-12:
                        raise AssertionError("Current grouped CV was not reproduced")
                    item["current_cv_reproduced"] = True
                records.append(item)
                print(json.dumps(item), flush=True)
                (args.output / "partial_results.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest for path, digest in originals.items())
    result = {
        "scope": (
            "Controlled diagnostics on fixed curated chemistry and current hyperparameters; "
            "not a recreation of every historical experiment."
        ),
        "cipw_recalculated": False,
        "models_exported": False,
        "originals_unchanged": True,
        "warning": "All-curated scenarios reuse the historical holdout and are not a new external or independent test.",
        "random_state": RANDOM_STATE,
        "folds": 5,
        "source_hashes": originals,
        "results": records,
    }
    (args.output / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    pd.DataFrame(predictions).to_csv(args.output / "oof_predictions.csv", index=False)


if __name__ == "__main__":
    main()
