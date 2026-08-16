from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from geonormml.config import (
    ARTIFACTS_DIR,
    ID_COLUMN,
    MANIFESTS_DIR,
    SPLITS_DIR,
    TARGET_COLUMN,
    setup_logging,
)
from geonormml.data import load_training_dataset
from geonormml.features import FEATURE_SETS, validate_feature_columns
from geonormml.split import make_cv_folds, make_holdout_split


logger = setup_logging("build_modeling_artifacts")


def main() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
    SPLITS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_training_dataset()
    missing = validate_feature_columns(df)
    if missing:
        raise ValueError(f"Missing columns in feature definitions: {missing}")

    manifest_rows = []
    for feature_set in FEATURE_SETS.values():
        manifest_rows.append(
            {
                "feature_set": feature_set.name,
                "n_features": len(feature_set.columns),
                "columns": ", ".join(feature_set.columns),
            }
        )

    manifest_df = pd.DataFrame(manifest_rows)
    manifest_path = MANIFESTS_DIR / "feature_sets.csv"
    manifest_df.to_csv(manifest_path, index=False, encoding="utf-8-sig")

    target_frequency = (
        df[TARGET_COLUMN].value_counts().rename_axis(TARGET_COLUMN).reset_index(name="count")
    )
    target_frequency_path = MANIFESTS_DIR / "target_frequency.csv"
    target_frequency.to_csv(target_frequency_path, index=False, encoding="utf-8-sig")

    holdout = make_holdout_split(df, id_column=ID_COLUMN)
    holdout_payload = {
        "train_ids": holdout.train_ids,
        "test_ids": holdout.test_ids,
    }
    holdout_path = SPLITS_DIR / "holdout_split.json"
    holdout_path.write_text(json.dumps(holdout_payload, indent=2), encoding="utf-8")

    cv_folds = make_cv_folds(df, id_column=ID_COLUMN)
    cv_path = SPLITS_DIR / "cv_folds.json"
    cv_path.write_text(json.dumps(cv_folds, indent=2), encoding="utf-8")

    summary_lines = [
        f"rows: {len(df)}",
        f"classes: {df[TARGET_COLUMN].nunique()}",
        f"holdout_train: {len(holdout.train_ids)}",
        f"holdout_test: {len(holdout.test_ids)}",
        "",
        "feature_sets:",
        manifest_df.to_string(index=False),
    ]
    summary_path = ARTIFACTS_DIR / "modeling_artifacts_summary.txt"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    logger.info(manifest_path)
    logger.info(target_frequency_path)
    logger.info(holdout_path)
    logger.info(cv_path)
    logger.info(summary_path)
    logger.info("\n".join(summary_lines))


if __name__ == "__main__":
    main()
