"""Prespecified expanded candidate space and group-level paired diagnostics."""

from copy import deepcopy

import numpy as np
import pandas as pd
from sklearn.base import clone

from .data import derive_features
from .features import CIPW_DERIVED_FEATURES, CIPW_FEATURES, FEATURE_SETS, PETROCHEM_CONTEXT_FEATURES
from .generation import PROFILES
from .ml import build_models, build_preprocessor

SPATIAL = {"combined_enriched_spatial", "combined_enriched_geodata", "combined_full"}
INDEPENDENT = {"oxides_core", "oxides"}
VARIANTS = {
    "RandomForest": {
        "original": {},
        "regularized": {"rf__min_samples_leaf": 3, "rf__max_features": 0.7},
    },
    "XGBoost": {
        "original": {},
        "shallow": {"xgb__max_depth": 3, "xgb__n_estimators": 400, "xgb__learning_rate": 0.03},
    },
    "SVM_PCA": {"original": {}, "C10": {"svc__C": 10.0}},
}


def specifications():
    specs = []
    for family, definition in FEATURE_SETS.items():
        for profile in ((None,) if family in INDEPENDENT else PROFILES):
            for algorithm, variants in VARIANTS.items():
                for variant, parameters in variants.items():
                    if family in SPATIAL and variant != "original":
                        continue
                    specs.append({
                        "id": f"{family}__{profile or 'no_norm'}__{algorithm}__{variant}",
                        "family": family, "profile": profile, "algorithm": algorithm,
                        "variant": variant, "parameters": parameters,
                        "columns": list(definition.columns),
                        "scope": "spatial_diagnostic" if family in SPATIAL else "transfer_candidate",
                        "order": len(specs),
                    })
    return specs


def profile_frame(data, norms):
    """Recompute every dependent index from this profile, never historical CIPW."""
    stale = [*CIPW_FEATURES, *CIPW_DERIVED_FEATURES, *PETROCHEM_CONTEXT_FEATURES, "Alc", "Trench_Dist"]
    frame = data.drop(columns=stale, errors="ignore").copy()
    for phase in CIPW_FEATURES:
        frame[phase] = norms.get("phase_" + phase, pd.Series(0.0, index=norms.index)).reindex(frame.index).fillna(0)
    frame["Ap"] += norms.get("phase_FAp", pd.Series(0.0, index=norms.index)).reindex(frame.index).fillna(0)
    frame = derive_features(frame)
    # sklearn SimpleImputer expects object categories, not pandas categorical NaNs.
    for column in PETROCHEM_CONTEXT_FEATURES:
        frame[column] = frame[column].astype(object)
    return frame


def estimator_for(spec, frame, n_classes):
    estimator = build_models(n_classes, build_preprocessor(spec["columns"], frame))[spec["algorithm"]]
    return clone(estimator).set_params(**deepcopy(spec["parameters"]))


def score_arrays(actual, predicted, n_classes):
    matrix = np.bincount(
        np.asarray(actual, dtype=int) * n_classes + np.asarray(predicted, dtype=int),
        minlength=n_classes * n_classes,
    ).reshape(n_classes, n_classes)
    diagonal = matrix.diagonal().astype(float)
    true = matrix.sum(axis=1).astype(float)
    guessed = matrix.sum(axis=0).astype(float)
    denom = true + guessed
    f1 = np.divide(2 * diagonal, denom, out=np.zeros(n_classes), where=denom > 0)
    recall = np.divide(diagonal, true, out=np.zeros(n_classes), where=true > 0)
    total = matrix.sum()
    mcc_denom = (total * total - np.dot(guessed, guessed)) * (total * total - np.dot(true, true))
    return {"accuracy": float(diagonal.sum() / total), "f1_macro": float(f1.mean()),
            "balanced_accuracy": float(recall[true > 0].mean()),
            "mcc": float((diagonal.sum() * total - np.dot(true, guessed)) / np.sqrt(mcc_denom))
            if mcc_denom > 0 else 0.0}


def best_record(records):
    return sorted(records, key=lambda r: (
        -r["f1_macro"], -r["mcc"], -r["accuracy"], r["feature_count"], r["order"],
    ))[0]


def paired_diagnostic(actual, left, right, groups, n_classes, repeats=1999, seed=42):
    """Swap complete groups of paired OOF predictions; exploratory, not a fresh test."""
    actual, left, right = (np.asarray(a, dtype=int) for a in (actual, left, right))
    unique, membership = np.unique(np.asarray(groups), return_inverse=True)
    rng = np.random.default_rng(seed)
    observed = score_arrays(actual, left, n_classes)["f1_macro"] - score_arrays(actual, right, n_classes)["f1_macro"]
    extreme = 0
    for _ in range(repeats):
        swap = rng.integers(0, 2, len(unique)).astype(bool)[membership]
        a, b = np.where(swap, right, left), np.where(swap, left, right)
        delta = score_arrays(actual, a, n_classes)["f1_macro"] - score_arrays(actual, b, n_classes)["f1_macro"]
        extreme += abs(delta) >= abs(observed) - 1e-15
    return {"delta_macro_f1": observed, "two_sided_group_swap_p": (extreme + 1) / (repeats + 1),
            "permutations": repeats, "groups": len(unique),
            "interpretation": ("Exploratory paired OOF diagnostic. Shared training folds and prior inspection "
                               "prevent confirmatory inference.")}
