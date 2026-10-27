"""Bounded model alternatives and explicit partition sensitivity, separate from frozen v4."""

import hashlib

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.decomposition import PCA
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

from .features import FEATURE_SETS
from .ml import build_preprocessor
from .quality import sample_groups

SEEDS = (42, 137, 2026)
ALGORITHMS = ("RandomForest", "XGBoost", "SVM", "ExtraTrees", "HistGB", "CatBoost", "Logistic")
VARIANTS = {
    "RandomForest": {
        "depth12": {"max_depth": 12, "min_samples_leaf": 2, "max_features": 0.5},
        "leaf6": {"max_depth": 20, "min_samples_leaf": 6, "max_features": 0.7},
        "reference_leaf3": {"min_samples_leaf": 3, "max_features": 0.7},
    },
    "XGBoost": {
        "balanced_shallow": {"max_depth": 3, "min_child_weight": 5, "reg_lambda": 5,
                             "reg_alpha": 0.1, "learning_rate": 0.03, "n_estimators": 400},
        "regularized": {"max_depth": 5, "min_child_weight": 3, "reg_lambda": 10, "reg_alpha": 0.5},
        "reference_original": {},
    },
    "SVM": {
        "without_pca": {"C": 10.0, "gamma": "scale", "pca": None},
        "pca99_gamma001": {"C": 10.0, "gamma": 0.01, "pca": 0.99},
        "reference_pca95_C10": {"C": 10.0, "gamma": "scale", "pca": 0.95},
    },
    "ExtraTrees": {
        "leaf1": {"min_samples_leaf": 1, "max_features": 0.7},
        "leaf3": {"min_samples_leaf": 3, "max_features": 1.0},
    },
    "HistGB": {
        "balanced15": {"max_leaf_nodes": 15, "min_samples_leaf": 10,
                       "l2_regularization": 1.0, "class_weight": "balanced"},
        "regular31": {"max_leaf_nodes": 31, "min_samples_leaf": 20,
                      "l2_regularization": 10.0, "class_weight": None},
    },
    "CatBoost": {
        "balanced4": {"depth": 4, "iterations": 250, "auto_class_weights": "Balanced", "l2_leaf_reg": 5},
        "sqrt6": {"depth": 6, "iterations": 350, "auto_class_weights": "SqrtBalanced", "l2_leaf_reg": 10},
    },
    "Logistic": {"C01": {"C": 0.1}, "C1": {"C": 1.0}},
}


def specifications():
    specs = []
    for family, profile in (("oxides_core", None), ("combined_contextual", "verma2003")):
        for algorithm, variants in VARIANTS.items():
            for variant, parameters in variants.items():
                specs.append({"id": f"{family}__{algorithm}__{variant}", "family": family,
                              "profile": profile, "algorithm": algorithm, "variant": variant,
                              "parameters": parameters, "columns": list(FEATURE_SETS[family].columns),
                              "weighted": algorithm == "XGBoost" and variant == "balanced_shallow",
                              "order": len(specs)})
    return specs


def seeded_folds(frame, n_splits, seed):
    """Vary the partition seed without varying the estimator random seed."""
    groups = sample_groups(frame)
    labels = frame["ROCK TYPE"].astype(str) + "::" + frame.ROCK_NAME.astype(str)
    counts = pd.DataFrame({"label": labels, "group": groups}).drop_duplicates().groupby("label").size()
    if counts.min() < n_splits:
        raise ValueError(f"Insufficient independent groups for {n_splits} folds: {counts.to_dict()}")
    folds = list(StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed).split(frame, labels, groups))
    for train, valid in folds:
        if set(groups.iloc[train]) & set(groups.iloc[valid]):
            raise ValueError("Replicate group leakage")
        if set(labels.iloc[train]) != set(labels):
            raise ValueError("Training fold missing a class; do not silently change the protocol")
    return folds


class CatInput(TransformerMixin, BaseEstimator):
    """Keep native categorical features and numeric NaNs; no target-based preprocessing."""

    def __init__(self, categorical=()):
        self.categorical = categorical

    def fit(self, X, y=None):
        self.columns_ = list(X)
        return self

    def transform(self, X):
        frame = X.loc[:, self.columns_].copy()
        for column in frame:
            if column in self.categorical:
                frame[column] = frame[column].fillna("__missing__").astype(str)
            else:
                frame[column] = pd.to_numeric(frame[column], errors="raise").astype(float)
        return frame


def estimator_for(spec, frame, n_classes):
    algorithm, parameters = spec["algorithm"], dict(spec["parameters"])
    if algorithm == "CatBoost":
        from catboost import CatBoostClassifier

        categorical = tuple(c for c in spec["columns"] if c in ("Clase_SiO2", "Serie_Mag"))
        return Pipeline([
            ("inputs", CatInput(categorical)),
            ("classifier", CatBoostClassifier(
                loss_function="MultiClass", learning_rate=0.05, random_seed=42, thread_count=1,
                allow_writing_files=False, verbose=False, nan_mode="Min", cat_features=list(categorical),
                **parameters,
            )),
        ])
    steps = [("preprocessor", build_preprocessor(spec["columns"], frame))]
    if algorithm == "RandomForest":
        classifier = RandomForestClassifier(n_estimators=400, class_weight="balanced_subsample",
                                            random_state=42, n_jobs=1, **parameters)
    elif algorithm == "ExtraTrees":
        classifier = ExtraTreesClassifier(n_estimators=400, class_weight="balanced", random_state=42,
                                          n_jobs=1, **parameters)
    elif algorithm == "HistGB":
        # Disable hidden random validation inside the estimator: groups remain under our control.
        classifier = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.05, early_stopping=False,
                                                     categorical_features=None, random_state=42, **parameters)
    elif algorithm == "XGBoost":
        defaults = {"n_estimators": 300, "max_depth": 6, "learning_rate": 0.05,
                    "subsample": 0.9, "colsample_bytree": 0.9}
        defaults.update(parameters)
        objective = {"objective": "binary:logistic", "eval_metric": "logloss"} if n_classes == 2 else {
            "objective": "multi:softprob", "num_class": n_classes, "eval_metric": "mlogloss"
        }
        classifier = XGBClassifier(tree_method="hist", random_state=42, n_jobs=1, **objective, **defaults)
    elif algorithm == "SVM":
        steps.append(("scaler", StandardScaler()))
        pca = parameters.pop("pca")
        if pca is not None:
            steps.append(("pca", PCA(n_components=pca, random_state=42)))
        # Prediction-only benchmarking: probability calibration requires its own grouped protocol.
        classifier = SVC(kernel="rbf", class_weight="balanced", probability=False,
                         random_state=42, **parameters)
    elif algorithm == "Logistic":
        steps.append(("scaler", StandardScaler()))
        classifier = LogisticRegression(class_weight="balanced", max_iter=2000, random_state=42, **parameters)
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    return Pipeline([*steps, ("classifier", classifier)])


def fit_model(spec, frame, target, n_classes):
    estimator = estimator_for(spec, frame, n_classes)
    kwargs = {"classifier__sample_weight": compute_sample_weight("balanced", target)} if spec["weighted"] else {}
    return estimator.fit(frame[spec["columns"]], target, **kwargs)


def predict_encoded(model, frame):
    predicted = np.asarray(model.predict(frame))
    if predicted.ndim > 1 and predicted.shape[1] != 1:
        raise ValueError("Expected one class label per row, received a class matrix")
    return predicted.reshape(-1).astype(int)


def geography_groups(frame):
    """Two-degree cells joined whenever a replicate group crosses cell boundaries."""
    valid = frame.LON.between(-180, 180) & frame.LAT.between(-90, 90)
    selected = frame.loc[valid]
    cells = list(zip(np.floor(selected.LON / 2).astype(int), np.floor(selected.LAT / 2).astype(int)))
    parent = {cell: cell for cell in cells}

    def find(cell):
        while parent[cell] != cell:
            parent[cell] = parent[parent[cell]]
            cell = parent[cell]
        return cell

    by_group = {}
    for group, cell in zip(selected.Sample_Group, cells):
        if group in by_group:
            left, right = find(cell), find(by_group[group])
            parent[max(left, right)] = min(left, right)
        else:
            by_group[group] = cell
    names = ["cell-" + hashlib.sha256(repr(find(cell)).encode()).hexdigest()[:12] for cell in cells]
    return pd.Series(names, index=selected.index, name="geographic_group")
