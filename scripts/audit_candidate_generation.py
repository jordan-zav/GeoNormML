"""Read-only audit of a completed candidate generation; never fits or replaces models."""

import argparse
import json
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report

from geonormml.config import ARTIFACTS_DIR, get_dataset_path
from geonormml.data import load_training_dataset
from geonormml.features import FEATURE_SETS, OXIDE_FEATURES_CORE
from geonormml.generation import dump_json, result_metrics, sha256
from geonormml.ml import build_models, build_preprocessor
from geonormml.quality import sample_groups
from geonormml.split import grouped_cv_indices


def ranked(records):
    return sorted(records, key=lambda r: (
        -r["f1_macro"], -r["mcc"], -r["accuracy"], r["feature_count"], r["order"],
    ))[0]["id"]


def audit(root):
    root = Path(root)
    plan = json.loads((root / "frozen_plan.json").read_text(encoding="utf-8"))
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    assert summary["complete"] and summary["originals_unchanged"]
    assert sha256(root / "frozen_plan.json") == summary["plan_sha256"]
    assert sha256(get_dataset_path()) == plan["dataset_sha256"]
    source = Path(__file__).resolve().parents[1]
    assert sha256(source / "scripts/train_candidate_generation.py") == plan["runner_sha256"]
    assert sha256(source / "src/geonormml/generation.py") == plan["selector_sha256"]
    originals = json.loads((root / "source_hashes.json").read_text(encoding="utf-8"))
    assert all(sha256(path) == expected for path, expected in originals.items())
    data = load_training_dataset().set_index("ID_Final", drop=False)
    data["Sample_Group"] = sample_groups(data)
    population = pd.read_csv(root / "population.csv").set_index("ID_Final", drop=False)
    assert population.index.is_unique and set(population.index) == set(data.index)
    assert population.Sample_Group.eq(data.Sample_Group).all()
    assert (population.original_training ^ population.original_holdout).all()
    recorded = json.loads((ARTIFACTS_DIR / "splits/holdout_split.json").read_text(encoding="utf-8"))
    assert set(population.index[population.original_training]) == set(recorded["train_ids"])
    assert set(population.index[population.original_holdout]) == set(recorded["test_ids"])
    common = pd.Series(True, index=data.index)
    coverage = {}
    for profile in plan["profiles"]:
        rows = pd.read_csv(root / f"{profile}_norms.csv").set_index("ID_Final")
        assert rows.index.is_unique and set(rows.index) == set(data.index)
        assert rows.complete.eq(rows.status.eq("complete")).all()
        common &= rows.complete.reindex(data.index)
        coverage[profile] = rows.status.value_counts().to_dict()
    assert common.eq(population.eligible_common).all()
    assert int(common.sum()) == summary["eligible_rows"]
    predictions = pd.read_csv(root / "nested_oof_predictions.csv")
    assert predictions.ID_Final.is_unique
    folds = json.loads((root / "outer_splits.json").read_text(encoding="utf-8"))
    domains = []
    for item in summary["models"]:
        domain = item["domain_code"]
        eligible = data.loc[common & data["ROCK TYPE"].eq(domain)]
        development = eligible.loc[eligible.index.isin(recorded["train_ids"])]
        heldout = eligible.loc[eligible.index.isin(recorded["test_ids"])]
        assert not set(development.Sample_Group) & set(heldout.Sample_Group)
        oof = predictions.loc[predictions.domain.eq(domain)].set_index("ID_Final")
        assert set(oof.index) == set(development.index)
        assert oof.actual.eq(data.loc[oof.index, "ROCK_NAME"]).all()
        classes = sorted(development.ROCK_NAME.unique())
        encoding = {label: i for i, label in enumerate(classes)}
        metrics = result_metrics(oof.actual.map(encoding), oof.predicted.map(encoding), len(classes))
        for name, value in metrics.items():
            assert np.isclose(value, item["validation"][name], rtol=0, atol=1e-12)
        selections = json.loads((root / f"{domain}_outer_selections.json").read_text(encoding="utf-8"))
        expected_specs = {r["id"] for r in item["selection_scores"]}
        assert ranked(item["selection_scores"]) == item["selected"]["id"]
        domain_folds = [f for f in folds if f["domain"] == domain]
        assert len(domain_folds) == plan["outer_folds"] == len(selections)
        reconstructed = grouped_cv_indices(development, n_splits=plan["outer_folds"])
        for fold, selected, (train, valid) in zip(domain_folds, selections, reconstructed):
            assert set(fold["train_ids"]) == set(development.iloc[train].index)
            assert set(fold["valid_ids"]) == set(development.iloc[valid].index)
            assert not set(data.loc[fold["train_ids"], "Sample_Group"]) & set(
                data.loc[fold["valid_ids"], "Sample_Group"]
            )
            assert set(oof.index[oof.fold.eq(fold["outer_fold"])]) == set(fold["valid_ids"])
            assert selected["fold"] == fold["outer_fold"]
            assert {r["id"] for r in selected["inner_scores"]} == expected_specs
            assert ranked(selected["inner_scores"]) == selected["selected"]["id"]
            # Reconstruct every inner split and check group disjointness without refitting.
            grouped_cv_indices(data.loc[fold["train_ids"]], n_splits=plan["inner_folds"])
        path = root / item["artifact_path"]
        assert sha256(path) == item["artifact_sha256"]
        bundle = joblib.load(path)  # Trusted local artifact, checksum verified above.
        assert bundle["generation_id"] == summary["generation_id"]
        assert bundle["feature_columns"] == item["feature_columns"]
        assert list(bundle["label_encoder"].classes_) == item["classes"] == classes
        assert bundle["fit_rows"] == len(eligible)
        model = bundle["estimator"].steps[-1][1]
        template = build_models(len(classes), build_preprocessor(OXIDE_FEATURES_CORE, data))[
            item["selected"]["model_name"]
        ].steps[-1][1]
        keys = ("n_estimators", "random_state", "class_weight", "max_depth", "learning_rate",
                "subsample", "colsample_bytree", "tree_method", "n_jobs", "objective", "num_class")
        params = {key: value for key, value in model.get_params().items() if key in keys}
        assert params == {key: value for key, value in template.get_params().items() if key in keys}
        domains.append({
            "domain": domain, "nested_metrics_recomputed": metrics,
            "outer_selected_counts": dict(Counter(s["selected"]["id"] for s in selections)),
            "final_selected": item["selected"], "parameters_match_repository_definition": params,
            "per_class_oof": classification_report(oof.actual, oof.predicted, labels=classes,
                                                   output_dict=True, zero_division=0),
            "eligible": len(eligible), "excluded_by_common_coverage": int(
                (data["ROCK TYPE"].eq(domain) & ~common).sum()
            ),
        })
    available = build_models(2, build_preprocessor(OXIDE_FEATURES_CORE, data))
    legacy_parameters = []
    for path in sorted((ARTIFACTS_DIR / "official_models").glob("*.joblib")):
        previous = joblib.load(path)  # Original artifacts were verified against run hashes.
        model = previous["estimator"].steps[-1][1]
        algorithm = "RandomForest" if model.__class__.__name__ == "RandomForestClassifier" else "XGBoost"
        template = available[algorithm].steps[-1][1]
        # Class count depends on domain; compare algorithm settings separately.
        keys = ("n_estimators", "random_state", "class_weight", "max_depth", "learning_rate",
                "subsample", "colsample_bytree", "tree_method", "n_jobs", "objective")
        params = {key: value for key, value in model.get_params().items() if key in keys}
        expected = {key: value for key, value in template.get_params().items() if key in keys}
        legacy_parameters.append({"file": path.name, "algorithm": algorithm, "parameters": params,
                                  "matches_current_builder": params == expected})
    return {
        "generation_id": summary["generation_id"], "audit_status": "scoped_results_verified_comparison_incomplete",
        "original_files_verified": len(originals), "coverage": coverage, "domains": domains,
        "previous_official_artifact_parameters": legacy_parameters,
        "configured_algorithms": list(available), "executed_algorithms": plan["algorithms"],
        "omitted_algorithms": sorted(set(available) - set(plan["algorithms"])),
        "configured_feature_sets": list(FEATURE_SETS), "executed_feature_sets": plan["features"],
        "omitted_feature_sets": sorted(set(FEATURE_SETS) - set(plan["features"])),
        "limits": [
            "No retraining or hyperparameter search performed by this audit.",
            "Saved inner scores checked for consistency, not independently refitted.",
            "Nested metrics evaluate selection procedure, not independent performance of final weights.",
            "Historical holdout already inspected; final weights include it in refit.",
            "Frozen plan hashes runner and selector, not all imported training modules or all estimator parameters.",
            "Full algorithm/feature benchmark and external validation remain pending.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Audit evidence must use a new output path")
    result = audit(args.run)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    dump_json(args.output, result)
    print(json.dumps({key: result[key] for key in ("audit_status", "original_files_verified", "omitted_algorithms")}))


if __name__ == "__main__":
    main()
