"""Explicit feature contracts and group-safe selection for candidate generations."""

import hashlib
import json
from pathlib import Path

import numpy as np
from sklearn.base import clone
from sklearn.metrics import accuracy_score, f1_score, matthews_corrcoef

from .features import CIPW_FEATURES, OXIDE_FEATURES_CORE
from .ml import build_models, build_preprocessor
from .split import grouped_cv_indices

GENERATION_ID = "profiles_nested_v3_20261026"
PROFILES = ("extended_cipw_v3", "verma2003", "pruseth2009")
MAJORS = ("SiO2", "TiO2", "Al2O3", "FeOT", "CaO", "MgO", "MnO", "Na2O", "K2O", "P2O5")
INPUT_KEYS = (*MAJORS, "CO2", "F", "Cl", "SO3", "S", "ZrO2", "Cr2O3")
PLAN = {
    "generation_id": GENERATION_ID,
    "release_status": "candidate_internal_validation_external_pending",
    "outer_folds": 5,
    "inner_folds": 3,
    "final_selection_folds": 5,
    "seed": 42,
    "selection_order": ["f1_macro", "mcc", "accuracy", "fewer_features", "candidate_order"],
    "algorithms": ["RandomForest", "XGBoost"],
    "profiles": list(PROFILES),
    "features": ["oxides_core", "combined_core"],
    "population": "Common complete profile population, preserved original sample groups and recorded split.",
    "holdout": "Historical inspected holdout: descriptive only; excluded from nested and final selection.",
    "cipw": {
        "required_engine_version": "1.1.0",
        "input_keys": list(INPUT_KEYS),
        "required_measured_majors": list(MAJORS),
        "optional_missing": "omitted",
        "outside_contract": "Not supplied; no LOI or NiO supplied as a normative input.",
        "iron_policy": "fixed",
        "fe3_fraction": 0.15,
        "carbonate_mode": "calcite",
        "carbonate_warning": "Calcite allocation is a fixed comparison assumption, not measured carbonate mineralogy.",
        "strict": False,
        "mass_tol": 1e-6,
        "apatite_feature": "Ap = Ap + FAp; raw phase identities remain separately recorded.",
    },
    "promotion": "No automatic production replacement or claim of external validation.",
}


def candidate_specs():
    choices = []
    for profile in (None, *PROFILES):
        for algorithm in PLAN["algorithms"]:
            choices.append(
                {
                    "id": f"{profile or 'oxides_only'}__{algorithm}",
                    "profile": profile,
                    "feature_set": "combined_core" if profile else "oxides_core",
                    "model_name": algorithm,
                }
            )
    return choices


def columns_for(spec):
    return list(OXIDE_FEATURES_CORE) + (list(CIPW_FEATURES) if spec["profile"] else [])


def result_metrics(actual, predicted, n_classes):
    return {
        "accuracy": float(accuracy_score(actual, predicted)),
        "f1_macro": float(f1_score(actual, predicted, labels=np.arange(n_classes), average="macro", zero_division=0)),
        "mcc": float(matthews_corrcoef(actual, predicted)),
    }


def template_for(spec, frame, n_classes):
    return build_models(n_classes, build_preprocessor(columns_for(spec), frame))[spec["model_name"]]


def select_candidate(frames, population, encoded_target, n_classes, folds, progress=None):
    """Select only from OOF predictions of the supplied inner-training population."""
    splits = grouped_cv_indices(population, n_splits=folds)
    records = []
    for order, spec in enumerate(candidate_specs()):
        frame = frames[spec["profile"]].loc[population.index]
        columns = columns_for(spec)
        predicted = np.full(len(frame), -1, dtype=int)
        seen = np.zeros(len(frame), dtype=int)
        template = template_for(spec, frame, n_classes)
        for train, valid in splits:
            estimator = clone(template).fit(frame.iloc[train][columns], encoded_target[train])
            predicted[valid] = estimator.predict(frame.iloc[valid][columns])
            seen[valid] += 1
        if not (seen == 1).all() or (predicted < 0).any():
            raise ValueError("Incomplete or repeated inner OOF predictions")
        item = {
            **spec,
            **result_metrics(encoded_target, predicted, n_classes),
            "feature_count": len(columns),
            "order": order,
        }
        records.append(item)
        if progress:
            progress(item)
    ranking = sorted(records, key=lambda r: (-r["f1_macro"], -r["mcc"], -r["accuracy"], r["feature_count"], r["order"]))
    selected = next(spec for spec in candidate_specs() if spec["id"] == ranking[0]["id"])
    return selected, records


def dump_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
