"""Shared ML model definitions and preprocessing utilities.

This module centralises the pipeline construction logic so that benchmark,
export and SHAP scripts all share the same model specifications without
cross-importing from ``scripts/``.
"""

from __future__ import annotations

import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC
from xgboost import XGBClassifier

from .config import RANDOM_STATE


def build_preprocessor(
    feature_columns: list[str],
    df: pd.DataFrame,
) -> ColumnTransformer:
    """Build a ColumnTransformer that imputes + encodes features.

    Numeric columns are imputed with median; categorical columns use an
    explicit missing-value label and are then one-hot encoded.
    """
    categorical_columns = [
        col
        for col in feature_columns
        if pd.api.types.is_object_dtype(df[col])
        or pd.api.types.is_string_dtype(df[col])
        or isinstance(df[col].dtype, pd.CategoricalDtype)
    ]
    numeric_columns = [col for col in feature_columns if col not in categorical_columns]

    transformers: list[tuple] = []
    if numeric_columns:
        transformers.append(
            (
                "numeric",
                SimpleImputer(strategy="median", keep_empty_features=True),
                numeric_columns,
            )
        )
    if categorical_columns:
        transformers.append(
            (
                "categorical",
                Pipeline(
                    steps=[
                        (
                            "imputer",
                            SimpleImputer(strategy="constant", fill_value="__missing__", keep_empty_features=True),
                        ),
                        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                    ]
                ),
                categorical_columns,
            )
        )

    return ColumnTransformer(transformers=transformers)


def build_models(
    n_classes: int,
    preprocessor: ColumnTransformer,
) -> dict[str, Pipeline]:
    """Return a dict of named sklearn Pipelines ready for fitting.

    Each pipeline includes a clone of *preprocessor* so they are independent.
    """
    xgb = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="multi:softprob",
        num_class=n_classes,
        eval_metric="mlogloss",
        tree_method="hist",
        random_state=RANDOM_STATE,
        n_jobs=1,
    )

    return {
        "RandomForest": Pipeline(
            steps=[
                ("preprocessor", clone(preprocessor)),
                (
                    "rf",
                    RandomForestClassifier(
                        n_estimators=400,
                        random_state=RANDOM_STATE,
                        class_weight="balanced_subsample",
                        n_jobs=1,
                    ),
                ),
            ]
        ),
        "SVM_PCA": Pipeline(
            steps=[
                ("preprocessor", clone(preprocessor)),
                ("scaler", StandardScaler()),
                ("pca", PCA(n_components=0.95, random_state=RANDOM_STATE)),
                (
                    "svc",
                    SVC(
                        kernel="rbf",
                        probability=True,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
        "XGBoost": Pipeline(
            steps=[
                ("preprocessor", clone(preprocessor)),
                ("xgb", xgb),
            ]
        ),
    }
