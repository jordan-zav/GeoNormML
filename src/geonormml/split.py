from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.model_selection import StratifiedKFold, train_test_split

from .config import CV_FOLDS, RANDOM_STATE, TARGET_COLUMN, TEST_SIZE


@dataclass(frozen=True)
class DatasetSplit:
    train_ids: list[int]
    test_ids: list[int]


def make_holdout_split(df: pd.DataFrame, id_column: str) -> DatasetSplit:
    train_ids, test_ids = train_test_split(
        df[id_column],
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=df[TARGET_COLUMN],
    )
    return DatasetSplit(
        train_ids=train_ids.tolist(),
        test_ids=test_ids.tolist(),
    )


def make_cv_folds(df: pd.DataFrame, id_column: str) -> list[dict[str, list[int]]]:
    skf = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    folds: list[dict[str, list[int]]] = []

    for fold_index, (train_idx, valid_idx) in enumerate(skf.split(df, df[TARGET_COLUMN]), start=1):
        fold = {
            "fold": fold_index,
            "train_ids": df.iloc[train_idx][id_column].tolist(),
            "valid_ids": df.iloc[valid_idx][id_column].tolist(),
        }
        folds.append(fold)

    return folds

