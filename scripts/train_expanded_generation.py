"""Expanded nested grouped comparison, isolated outputs and no production promotion."""

import argparse
import json
import os
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from importlib.metadata import version
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder

from geonormml.config import get_dataset_path
from geonormml.data import load_training_dataset
from geonormml.expanded import (
    best_record,
    estimator_for,
    paired_diagnostic,
    profile_frame,
    score_arrays,
    specifications,
)
from geonormml.generation import PROFILES, dump_json, sha256
from geonormml.quality import sample_groups
from geonormml.split import grouped_cv_indices

GENERATION = "expanded_nested_v4_20261027"


def json_safe(value):
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return repr(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return {"class": f"{type(value).__module__}.{type(value).__name__}", "repr": repr(value)}


def record_for(spec, actual, predicted, n_classes):
    return {"id": spec["id"], "algorithm": spec["algorithm"], "order": spec["order"],
            "feature_count": len(spec["columns"]), **score_arrays(actual, predicted, n_classes)}


def run_domain(domain, data, frames, membership, old_root, output, specs):
    directory = output / domain
    directory.mkdir(exist_ok=True)
    eligible = data.loc[membership.eligible_common & data["ROCK TYPE"].eq(domain)]
    development = eligible.loc[membership.loc[eligible.index, "original_training"]]
    encoder = LabelEncoder().fit(development.ROCK_NAME)
    target, n_classes = encoder.transform(development.ROCK_NAME), len(encoder.classes_)
    lookup = {spec["id"]: spec for spec in specs}
    candidates = [s for s in specs if s["scope"] == "transfer_candidate"]
    spatial = [s for s in specs if s["scope"] == "spatial_diagnostic"]
    procedures = ["all_candidates", "RandomForest", "XGBoost", "SVM_PCA"]
    oof = {name: np.full(len(development), -1, dtype=int) for name in procedures}
    spatial_oof = {s["id"]: np.full(len(development), -1, dtype=int) for s in spatial}
    dummy_oof = np.full(len(development), -1, dtype=int)
    chosen, saved_splits = [], []
    outer = grouped_cv_indices(development, n_splits=5)
    for fold, (train, valid) in enumerate(outer, start=1):
        inner = development.iloc[train]
        inner_splits = grouped_cv_indices(inner, n_splits=3)
        saved_splits.append({"fold": fold, "train_ids": inner.ID_Final.tolist(),
                             "valid_ids": development.iloc[valid].ID_Final.tolist(),
                             "inner": [{"train_ids": inner.iloc[a].ID_Final.tolist(),
                                        "valid_ids": inner.iloc[b].ID_Final.tolist()} for a, b in inner_splits]})
        records = []
        for index, spec in enumerate(candidates, start=1):
            key = directory / f"inner_{fold}_{index:03d}.json"
            if key.exists():
                record = json.loads(key.read_text(encoding="utf-8"))
                if record["id"] != spec["id"]:
                    raise ValueError("Checkpoint candidate mismatch")
            else:
                predicted = np.full(len(inner), -1, dtype=int)
                frame = frames[spec["profile"]].loc[inner.index]
                start = time.monotonic()
                for a, b in inner_splits:
                    fitted = estimator_for(spec, frame, n_classes).fit(frame.iloc[a][spec["columns"]], target[train][a])
                    predicted[b] = fitted.predict(frame.iloc[b][spec["columns"]])
                record = record_for(spec, target[train], predicted, n_classes)
                record["elapsed_seconds"] = time.monotonic() - start
                dump_json(key, record)
            records.append(record)
            print("INNER", domain, fold, index, len(candidates), spec["id"], round(record["f1_macro"], 5), flush=True)
        winners = {name: best_record(records if name == "all_candidates" else [
            r for r in records if r["algorithm"] == name
        ])["id"] for name in procedures}
        fitted_winners = {}
        for identifier in set(winners.values()):
            spec = lookup[identifier]
            frame = frames[spec["profile"]]
            fitted_winners[identifier] = estimator_for(spec, frame, n_classes).fit(
                frame.loc[inner.index, spec["columns"]], target[train]
            ).predict(frame.loc[development.iloc[valid].index, spec["columns"]])
        for name, identifier in winners.items():
            oof[name][valid] = fitted_winners[identifier]
        dummy = DummyClassifier(strategy="prior").fit(np.zeros((len(train), 1)), target[train])
        dummy_oof[valid] = dummy.predict(np.zeros((len(valid), 1)))
        for spec in spatial:
            frame = frames[spec["profile"]]
            fitted = estimator_for(spec, frame, n_classes).fit(frame.loc[inner.index, spec["columns"]], target[train])
            spatial_oof[spec["id"]][valid] = fitted.predict(frame.loc[development.iloc[valid].index, spec["columns"]])
        chosen.append({"fold": fold, "winners": winners, "inner_scores": records})
        dump_json(directory / "selections.json", chosen)
        dump_json(directory / "splits.json", saved_splits)
        print("OUTER_COMPLETE", domain, fold, winners, flush=True)
    results = []
    prediction_table = development[["ID_Final", "ROCK_NAME", "Sample_Group"]].copy()
    prediction_table["fold"] = -1
    for fold, (_, valid) in enumerate(outer, start=1):
        prediction_table.iloc[valid, prediction_table.columns.get_loc("fold")] = fold
    for name, predictions in {**oof, "dummy_prior": dummy_oof, **spatial_oof}.items():
        if (predictions < 0).any():
            raise ValueError("Missing OOF prediction")
        labels = encoder.inverse_transform(predictions)
        prediction_table[name] = labels
        results.append({"procedure": name, **score_arrays(target, predictions, n_classes),
                        "scope": ("nested_selection" if name in oof else
                                  "fixed_spatial_diagnostic" if name in spatial_oof else "dummy"),
                        "per_class": classification_report(development.ROCK_NAME, labels, labels=encoder.classes_,
                                                           zero_division=0, output_dict=True)})
    # Compare to prior procedure on exactly the same samples and outer folds.
    old = pd.read_csv(old_root / "nested_oof_predictions.csv")
    old = old.loc[old.domain.eq(domain)].set_index("ID_Final").loc[development.index]
    if not old.fold.eq(prediction_table.fold).all():
        raise ValueError("Previous OOF fold mismatch")
    previous = encoder.transform(old.predicted)
    prediction_table["previous_v3"] = old.predicted
    comparisons = {"expanded_vs_previous_v3": paired_diagnostic(
        target, oof["all_candidates"], previous, development.Sample_Group, n_classes
    )}
    for name in procedures[1:]:
        comparisons[f"expanded_vs_{name}"] = paired_diagnostic(
            target, oof["all_candidates"], oof[name], development.Sample_Group, n_classes
        )
    # Descriptive slice only: selection never routes by the unknown true rock label.
    slices = []
    for profile in PROFILES:
        series = frames[profile].loc[development.index, "Serie_Mag"]
        for label in sorted(series.dropna().unique()):
            mask = series.eq(label).to_numpy()
            for name in procedures:
                slices.append({"profile": profile, "derived_series": label, "rows": int(mask.sum()),
                               "procedure": name, **score_arrays(target[mask], oof[name][mask], n_classes)})
    # Final selection uses only development, and has exactly the same candidate space.
    final_scores = []
    final_splits = grouped_cv_indices(development, n_splits=5)
    dump_json(directory / "final_selection_splits.json", [
        {"train_ids": development.iloc[a].ID_Final.tolist(), "valid_ids": development.iloc[b].ID_Final.tolist()}
        for a, b in final_splits
    ])
    for index, spec in enumerate(candidates, start=1):
        key = directory / f"final_{index:03d}.json"
        if key.exists():
            record = json.loads(key.read_text(encoding="utf-8"))
            if record["id"] != spec["id"]:
                raise ValueError("Final checkpoint mismatch")
        else:
            predicted = np.full(len(development), -1, dtype=int)
            frame = frames[spec["profile"]].loc[development.index]
            for a, b in final_splits:
                fitted = estimator_for(spec, frame, n_classes).fit(frame.iloc[a][spec["columns"]], target[a])
                predicted[b] = fitted.predict(frame.iloc[b][spec["columns"]])
            record = record_for(spec, target, predicted, n_classes)
            dump_json(key, record)
        final_scores.append(record)
        print("FINAL", domain, index, len(candidates), spec["id"], round(record["f1_macro"], 5), flush=True)
    selected = lookup[best_record(final_scores)["id"]]
    final_frame = frames[selected["profile"]]
    fitted = estimator_for(selected, final_frame, n_classes).fit(
        final_frame.loc[eligible.index, selected["columns"]], encoder.transform(eligible.ROCK_NAME)
    )
    path = directory / "candidate.joblib"
    joblib.dump({"generation_id": GENERATION, "release_status": "experimental_external_pending",
                 "domain": domain, "selected": selected, "estimator": fitted,
                 "label_encoder": encoder, "feature_columns": selected["columns"],
                 "fit_rows": len(eligible), "plan_sha256": sha256(output / "frozen_plan.json")}, path)
    prediction_table.to_csv(directory / "oof_predictions.csv", index=False)
    report = {"domain": domain, "development_rows": len(development), "fit_rows": len(eligible),
              "results": results, "comparisons": comparisons, "series_slices": slices,
              "final_selection": selected, "final_selection_scores": final_scores,
              "outer_selected_counts": dict(Counter(c["winners"]["all_candidates"] for c in chosen)),
              "model_sha256": sha256(path), "external_validation": False}
    dump_json(directory / "summary.json", report)
    print("DOMAIN_COMPLETE", domain, selected["id"], flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, choices=(1, 2), default=1)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    if not args.resume:
        output.mkdir(parents=True, exist_ok=False)
    old_root = args.previous.resolve()
    previous = json.loads((old_root / "summary.json").read_text(encoding="utf-8"))
    previous_plan = json.loads((old_root / "frozen_plan.json").read_text(encoding="utf-8"))
    if not previous["complete"] or sha256(get_dataset_path()) != previous_plan["dataset_sha256"]:
        raise ValueError("Source dataset does not match previous completed generation")
    originals = json.loads((old_root / "source_hashes.json").read_text(encoding="utf-8"))
    if not all(sha256(p) == digest for p, digest in originals.items()):
        raise ValueError("Original data or baseline model changed")
    data = load_training_dataset().set_index("ID_Final", drop=False)
    data["Sample_Group"] = sample_groups(data)
    membership = pd.read_csv(old_root / "population.csv").set_index("ID_Final").loc[data.index]
    if not membership.Sample_Group.eq(data.Sample_Group).all():
        raise ValueError("Group identity mismatch")
    frames = {None: data.copy()}
    for profile in PROFILES:
        norms = pd.read_csv(old_root / f"{profile}_norms.csv").set_index("ID_Final")
        frames[profile] = profile_frame(data, norms)
    specs = specifications()
    root = Path(__file__).resolve().parents[1]
    import geonormpy
    code_files = [*list((root / "src").rglob("*.py")), Path(__file__),
                  *list(Path(geonormpy.__file__).parent.rglob("*.py"))]
    plan = {"generation_id": GENERATION, "status": "experimental_external_pending",
            "dataset_sha256": sha256(get_dataset_path()), "source_hashes": {str(p): sha256(p) for p in code_files},
            "input_hashes": {str(p): sha256(p) for p in old_root.glob("*.csv")},
            "specifications": specs, "outer_folds": 5, "inner_folds": 3, "final_selection_folds": 5,
            "seed": 42, "primary": "OOF macro F1, then MCC, accuracy, fewer columns, fixed order",
            "population": "Same 2701 common eligible IDs and original development partition as v3",
            "spatial": ("All nine profile/family combinations, three original algorithms; "
                        "diagnostic only, excluded from primary selection"),
            "holdout": ("Previously inspected; excluded from selection and included only in final refit; "
                        "no new blind test claimed"),
            "adaptation": ("Protocol expanded after inspecting v3; internal evidence only, "
                           "no confirmatory external claim"),
            "series": ("Profile-derived operational series, descriptive slices, "
                       "not independently measured affinity labels"),
            "permutations": ("1999 groupwise paired OOF prediction swaps; exploratory only, "
                             "no feature selection or labels shuffled; Holm across eight planned comparisons"),
            "cipw_contract": previous_plan["cipw"],
            "previous_plan_sha256": sha256(old_root / "frozen_plan.json"),
            "dependencies": {name: version(name) for name in (
                "numpy", "pandas", "scipy", "scikit-learn", "xgboost", "joblib", "geonormpy"
            )},
            "git_commit": os.popen("git rev-parse HEAD").read().strip(),
            "git_status": os.popen("git status --porcelain").read(), "parameters": {}}
    for domain in ("VOL", "PLU"):
        n_classes = data.loc[data["ROCK TYPE"].eq(domain), "ROCK_NAME"].nunique()
        plan["parameters"][domain] = {spec["id"]: json_safe(
            estimator_for(spec, frames[spec["profile"]], n_classes).get_params(deep=True)
        ) for spec in specs}
        for spec in specs:
            missing = set(spec["columns"]) - set(frames[spec["profile"]])
            if missing:
                raise ValueError(f"Missing columns for {spec['id']}: {missing}")
    plan_file = output / "frozen_plan.json"
    if args.resume:
        frozen = json.loads(plan_file.read_text(encoding="utf-8"))
        # A resume may see its own execution artifacts, but must retain all frozen source/data/configuration.
        for key in ("source_hashes", "input_hashes", "specifications", "parameters", "dataset_sha256", "dependencies"):
            if frozen[key] != plan[key]:
                raise ValueError(f"Cannot resume after changes to {key}")
    else:
        dump_json(plan_file, plan)
    print("PLAN_FROZEN", GENERATION, len(specs), "specs per domain", flush=True)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run_domain, domain, data, frames, membership, old_root, output, specs)
                   for domain in ("VOL", "PLU")]
        reports = [future.result() for future in futures]
    comparisons = [comparison for report in reports for comparison in report["comparisons"].values()]
    ordered = sorted(comparisons, key=lambda c: c["two_sided_group_swap_p"])
    running = 0.0
    for index, comparison in enumerate(ordered):
        running = max(running, (len(ordered) - index) * comparison["two_sided_group_swap_p"])
        comparison["holm_adjusted_p_eight_comparisons"] = min(1.0, running)
    if not all(sha256(p) == digest for p, digest in originals.items()):
        raise ValueError("Original resource changed during comparison")
    dump_json(output / "summary.json", {"generation_id": GENERATION, "complete": True,
                                       "original_files_unchanged": len(originals),
                                       "models": reports, "plan_sha256": sha256(plan_file)})
    print("EXPANDED_COMPLETE", output, flush=True)


if __name__ == "__main__":
    main()
