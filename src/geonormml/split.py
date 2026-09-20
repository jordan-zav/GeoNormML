from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from .config import CV_FOLDS, RANDOM_STATE, TARGET_COLUMN, TEST_SIZE
from .quality import sample_groups


@dataclass(frozen=True)
class DatasetSplit:
    train_ids: list[int]
    test_ids: list[int]


def grouped_cv_indices(df: pd.DataFrame, n_splits: int = CV_FOLDS):
    if df.empty or df[TARGET_COLUMN].isna().any():
        raise ValueError("Nonempty labeled data is required for validation.")
    if "ID_Final" in df and (df.ID_Final.isna().any() or df.ID_Final.duplicated().any()):
        raise ValueError("Unique, nonmissing ID_Final values are required for validation.")
    labels = df[TARGET_COLUMN].astype(str)
    if "ROCK TYPE" in df:
        labels = df["ROCK TYPE"].astype(str) + "::" + labels
    groups = sample_groups(df)
    counts = pd.DataFrame({"label": labels, "group": groups}).drop_duplicates().groupby("label").size()
    if counts.min() < n_splits:
        raise ValueError(f"At least {n_splits} sample groups per class are required: {counts.to_dict()}")
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
    folds = list(splitter.split(df, labels, groups))
    for train, valid in folds:
        if set(groups.iloc[train]) & set(groups.iloc[valid]):
            raise AssertionError("Sample group leakage detected.")
        if set(labels.iloc[train]) != set(labels):
            raise ValueError("A training fold is missing a class; revise sample grouping or reduce folds.")
    return folds


def make_holdout_split(df: pd.DataFrame, id_column: str) -> DatasetSplit:
    train, test = grouped_cv_indices(df, n_splits=round(1 / TEST_SIZE))[0]
    return DatasetSplit(df.iloc[train][id_column].tolist(), df.iloc[test][id_column].tolist())


def make_cv_folds(df: pd.DataFrame, id_column: str) -> list[dict[str, list[int]]]:
    folds: list[dict[str, list[int]]] = []

    for fold_index, (train_idx, valid_idx) in enumerate(grouped_cv_indices(df), start=1):
        fold = {
            "fold": fold_index,
            "train_ids": df.iloc[train_idx][id_column].tolist(),
            "valid_ids": df.iloc[valid_idx][id_column].tolist(),
        }
        folds.append(fold)

    return folds
