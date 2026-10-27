"""New model families, repeated partition seeds and fold-count sensitivity; isolated research output."""

import argparse
import json
import os
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from importlib.metadata import version
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.preprocessing import LabelEncoder

from geonormml.config import ARTIFACTS_DIR, get_dataset_path
from geonormml.data import load_training_dataset
from geonormml.expanded import best_record, profile_frame, score_arrays
from geonormml.generation import dump_json, sha256
from geonormml.quality import sample_groups
from geonormml.stability import (
    ALGORITHMS,
    SEEDS,
    estimator_for,
    fit_model,
    geography_groups,
    predict_encoded,
    seeded_folds,
    specifications,
)

GENERATION = "partition_stability_v5_20261027"
PROTOCOLS = [{"id": f"folds5_seed{seed}", "outer_folds": 5, "seed": seed} for seed in SEEDS]
PROTOCOLS.append({"id": "folds3_seed42", "outer_folds": 3, "seed": 42})


def canonical_parameters(value):
    if isinstance(value, dict):
        return {str(k): canonical_parameters(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [canonical_parameters(v) for v in value]
    if hasattr(value, "get_params") and not isinstance(value, type):
        return {"class": f"{type(value).__module__}.{type(value).__name__}",
                "parameters": canonical_parameters(value.get_params(deep=False))}
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return repr(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return {"class": f"{type(value).__module__}.{type(value).__name__}", "repr": repr(value)}


def inner_search(frames, population, target, n_classes, specs, folds, seed, directory):
    directory.mkdir(parents=True, exist_ok=True)
    splits = seeded_folds(population, folds, seed)
    dump_json(directory / "splits.json", [
        {"train_ids": population.iloc[a].ID_Final.tolist(), "valid_ids": population.iloc[b].ID_Final.tolist()}
        for a, b in splits
    ])
    records = []
    for index, spec in enumerate(specs, start=1):
        path = directory / f"candidate_{index:03d}.json"
        if path.exists():
            record = json.loads(path.read_text(encoding="utf-8"))
            if record["id"] != spec["id"] or len(record["predictions"]) != len(population):
                raise ValueError("Checkpoint differs from frozen search")
            predictions = np.asarray(record["predictions"], dtype=int)
        else:
            frame = frames[spec["profile"]].loc[population.index]
            predictions = np.full(len(population), -1, dtype=int)
            for train, valid in splits:
                fitted = fit_model(spec, frame.iloc[train], target[train], n_classes)
                predictions[valid] = predict_encoded(fitted, frame.iloc[valid][spec["columns"]])
            if (predictions < 0).any():
                raise ValueError("Incomplete inner OOF")
            record = {"id": spec["id"], "algorithm": spec["algorithm"], "order": spec["order"],
                      "feature_count": len(spec["columns"]), **score_arrays(target, predictions, n_classes),
                      "predictions": predictions.tolist()}
            dump_json(path, record)
        scores = score_arrays(target, predictions, n_classes)
        if any(not np.isclose(scores[k], record[k], rtol=0, atol=1e-12) for k in scores):
            raise ValueError("Checkpoint scores do not reproduce from OOF predictions")
        records.append(record)
        print("SEARCH", directory.parent.name, directory.name, index, len(specs), spec["id"],
              round(record["f1_macro"], 5), flush=True)
    return [{k: v for k, v in record.items() if k != "predictions"} for record in records]


def geographic_diagnostic(domain, development, frames, specs, directory):
    groups = geography_groups(development)
    selected = development.loc[groups.index]
    encoder = LabelEncoder().fit(development.ROCK_NAME)
    target = encoder.transform(selected.ROCK_NAME)
    count = len(encoder.classes_)
    if groups.nunique() < 3:
        return {"status": "insufficient_geographic_groups", "groups": int(groups.nunique())}
    folds = list(StratifiedGroupKFold(3, shuffle=True, random_state=42).split(selected, target, groups))
    fixed = {}
    for algorithm in ALGORITHMS:
        choices = [s for s in specs if s["algorithm"] == algorithm and s["family"] == "oxides_core"]
        fixed[algorithm] = next((s for s in choices if s["variant"].startswith("reference")), choices[0])
    predictions = {name: np.full(len(selected), -1, dtype=int) for name in fixed}
    audit = []
    for fold, (train, valid) in enumerate(folds, start=1):
        training, validation = selected.iloc[train], selected.iloc[valid]
        if (set(training.Sample_Group) & set(validation.Sample_Group)
                or set(groups.iloc[train]) & set(groups.iloc[valid])):
            raise ValueError("Geographic or replicate leakage")
        local_encoder = LabelEncoder().fit(training.ROCK_NAME)
        if len(local_encoder.classes_) < 2:
            return {"status": "insufficient_training_classes", "fold": fold}
        local_target = local_encoder.transform(training.ROCK_NAME)
        audit.append({"fold": fold, "train_ids": training.ID_Final.tolist(), "valid_ids": validation.ID_Final.tolist(),
                      "unseen_classes": sorted(set(validation.ROCK_NAME) - set(training.ROCK_NAME))})
        for algorithm, spec in fixed.items():
            fitted = fit_model(spec, frames[None].loc[training.index], local_target, len(local_encoder.classes_))
            local = predict_encoded(fitted, frames[None].loc[validation.index, spec["columns"]])
            predictions[algorithm][valid] = encoder.transform(local_encoder.inverse_transform(local))
        print("GEO", domain, fold, "of 3", flush=True)
    table = selected[["ID_Final", "ROCK_NAME", "Sample_Group"]].copy()
    table["geographic_group"] = groups
    for algorithm, prediction in predictions.items():
        table[algorithm] = encoder.inverse_transform(prediction)
    table.to_csv(directory / "geographic_oof.csv", index=False)
    dump_json(directory / "geographic_splits.json", audit)
    return {"status": "complete", "rows": len(selected), "groups": int(groups.nunique()),
            "missing_coordinate_rows": len(development) - len(selected), "fixed_specs": fixed,
            "results": [{"algorithm": name, **score_arrays(target, prediction, count)}
                        for name, prediction in predictions.items()],
            "unseen_classes_by_fold": [row["unseen_classes"] for row in audit],
            "interpretation": ("Fixed oxide-only specifications, no geographic hyperparameter selection. "
                               "Two-degree blocks are an internal stress test, not external validation.")}


def run_domain(domain, data, frames, membership, v4_root, output, specs):
    directory = output / domain
    directory.mkdir(exist_ok=True)
    eligible = data.loc[membership.eligible_common & data["ROCK TYPE"].eq(domain)]
    development = eligible.loc[membership.loc[eligible.index, "original_training"]]
    heldout = eligible.loc[membership.loc[eligible.index, "original_holdout"]]
    if set(development.Sample_Group) & set(heldout.Sample_Group):
        raise ValueError("Historical holdout leaks groups")
    encoder = LabelEncoder().fit(development.ROCK_NAME)
    target, count = encoder.transform(development.ROCK_NAME), len(encoder.classes_)
    lookup = {s["id"]: s for s in specs}
    v4 = joblib.load(v4_root / domain / "candidate.joblib")
    legacy_name = {"VOL": "volcanic__combined_core__XGBoost.joblib",
                   "PLU": "plutonic__combined_core__RandomForest.joblib"}[domain]
    incumbent = joblib.load(ARTIFACTS_DIR / "official_models" / legacy_name)
    protocols = []
    for protocol in PROTOCOLS:
        path = directory / protocol["id"]
        path.mkdir(exist_ok=True)
        if (path / "summary.json").exists():
            completed = json.loads((path / "summary.json").read_text(encoding="utf-8"))
            if (any(completed[key] != protocol[key] for key in ("id", "seed", "outer_folds"))
                    or completed["rows"] != len(development)
                    or completed["plan_sha256"] != sha256(output / "frozen_plan.json")
                    or completed["oof_sha256"] != sha256(path / "oof_predictions.csv")):
                raise ValueError("Completed protocol checkpoint failed integrity checks")
            protocols.append(completed)
            continue
        procedures = ["all_candidates", *ALGORITHMS, "incumbent_historical", "v4_frozen_refit", "dummy_prior"]
        predicted = {name: np.full(len(development), -1, dtype=int) for name in procedures}
        fold_assignment = np.full(len(development), -1, dtype=int)
        audits, selections = [], []
        for fold, (train, valid) in enumerate(seeded_folds(development, protocol["outer_folds"], protocol["seed"]), 1):
            inner = development.iloc[train]
            records = inner_search(frames, inner, target[train], count, specs, 3,
                                   protocol["seed"] + 10000 + fold, path / f"outer_{fold}")
            winners = {name: best_record(records if name == "all_candidates" else [
                r for r in records if r["algorithm"] == name
            ])["id"] for name in ["all_candidates", *ALGORITHMS]}
            cached = {}
            for identifier in set(winners.values()):
                spec = lookup[identifier]
                frame = frames[spec["profile"]]
                fitted = fit_model(spec, frame.loc[inner.index], target[train], count)
                cached[identifier] = predict_encoded(fitted, frame.loc[development.iloc[valid].index, spec["columns"]])
            for name, identifier in winners.items():
                predicted[name][valid] = cached[identifier]
            for name, bundle, frame in (("incumbent_historical", incumbent, data),
                                        ("v4_frozen_refit", v4, frames[v4["selected"]["profile"]])):
                fitted = clone(bundle["estimator"]).fit(
                    frame.loc[inner.index, bundle["feature_columns"]], target[train]
                )
                predicted[name][valid] = predict_encoded(
                    fitted, frame.loc[development.iloc[valid].index, bundle["feature_columns"]]
                )
            dummy = DummyClassifier(strategy="prior").fit(np.zeros((len(train), 1)), target[train])
            predicted["dummy_prior"][valid] = dummy.predict(np.zeros((len(valid), 1)))
            fold_assignment[valid] = fold
            audits.append({"fold": fold, "train_ids": inner.ID_Final.tolist(),
                           "valid_ids": development.iloc[valid].ID_Final.tolist()})
            selections.append({"fold": fold, "winners": winners})
            dump_json(path / "splits.json", audits)
            dump_json(path / "selections.json", selections)
            print("OUTER", domain, protocol["id"], fold, winners["all_candidates"], flush=True)
        table = development[["ID_Final", "ROCK_NAME", "Sample_Group"]].copy()
        table["fold"] = fold_assignment
        results = []
        for name, prediction in predicted.items():
            if (prediction < 0).any():
                raise ValueError("Incomplete outer OOF")
            labels = encoder.inverse_transform(prediction)
            table[name] = labels
            results.append({"procedure": name, **score_arrays(target, prediction, count),
                            "per_class": classification_report(development.ROCK_NAME, labels, labels=encoder.classes_,
                                                               zero_division=0, output_dict=True)})
        table.to_csv(path / "oof_predictions.csv", index=False)
        summary = {**protocol, "rows": len(development), "results": results,
                   "plan_sha256": sha256(output / "frozen_plan.json"),
                   "oof_sha256": sha256(path / "oof_predictions.csv"),
                   "selected_counts": dict(Counter(s["winners"]["all_candidates"] for s in selections))}
        dump_json(path / "summary.json", summary)
        protocols.append(summary)
        print("PROTOCOL_COMPLETE", domain, protocol["id"], flush=True)
    aggregate = []
    for name in [r["procedure"] for r in protocols[0]["results"]]:
        repeated = [next(r for r in p["results"] if r["procedure"] == name)
                    for p in protocols if p["outer_folds"] == 5]
        aggregate.append({"procedure": name, "seeds": list(SEEDS), **{
            metric: {"mean": float(np.mean([r[metric] for r in repeated])),
                     "sd_across_partitions": float(np.std([r[metric] for r in repeated], ddof=1)),
                     "min": float(min(r[metric] for r in repeated)), "max": float(max(r[metric] for r in repeated))}
            for metric in ("accuracy", "f1_macro", "mcc")
        }})
    final_scores = inner_search(frames, development, target, count, specs, 5, 42, directory / "final_selection")
    selected = lookup[best_record(final_scores)["id"]]
    fitted = fit_model(selected, frames[selected["profile"]].loc[eligible.index],
                       encoder.transform(eligible.ROCK_NAME), count)
    model_path = directory / "candidate.joblib"
    joblib.dump({"generation_id": GENERATION, "selected": selected, "estimator": fitted,
                 "label_encoder": encoder, "fit_rows": len(eligible), "status": "experimental_external_pending",
                 "plan_sha256": sha256(output / "frozen_plan.json")}, model_path)
    geography = geographic_diagnostic(domain, development, frames, specs, directory)
    result = {"domain": domain, "development_rows": len(development), "fit_rows": len(eligible),
              "protocols": protocols, "aggregate": aggregate, "final_selected": selected,
              "final_selection_scores": final_scores, "model_sha256": sha256(model_path),
              "geographic_diagnostic": geography}
    dump_json(directory / "summary.json", result)
    print("DOMAIN_COMPLETE", domain, selected["id"], flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--v4", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, choices=(1, 2), default=1)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    if not args.resume:
        output.mkdir(parents=True, exist_ok=False)
    previous, v4 = args.previous.resolve(), args.v4.resolve()
    v4_summary = json.loads((v4 / "summary.json").read_text(encoding="utf-8"))
    if not v4_summary["complete"] or any(
        sha256(v4 / item["domain"] / "candidate.joblib") != item["model_sha256"] for item in v4_summary["models"]
    ):
        raise ValueError("The previous expanded generation is incomplete or its model hash changed")
    old_plan = json.loads((previous / "frozen_plan.json").read_text(encoding="utf-8"))
    originals = json.loads((previous / "source_hashes.json").read_text(encoding="utf-8"))
    if sha256(get_dataset_path()) != old_plan["dataset_sha256"] or not all(
        sha256(p) == digest for p, digest in originals.items()
    ):
        raise ValueError("Dataset or original artifact changed")
    data = load_training_dataset().set_index("ID_Final", drop=False)
    data["Sample_Group"] = sample_groups(data)
    membership = pd.read_csv(previous / "population.csv").set_index("ID_Final").loc[data.index]
    if not membership.Sample_Group.eq(data.Sample_Group).all():
        raise ValueError("Replicate grouping changed")
    norms = pd.read_csv(previous / "verma2003_norms.csv").set_index("ID_Final")
    frames = {None: data, "verma2003": profile_frame(data, norms)}
    specs = specifications()
    root = Path(__file__).resolve().parents[1]
    import geonormpy
    source = [*list((root / "src").rglob("*.py")), Path(__file__),
              root / "scripts/train_expanded_generation.py", *list(Path(geonormpy.__file__).parent.rglob("*.py"))]
    inputs = [get_dataset_path(), previous / "population.csv", previous / "verma2003_norms.csv",
              previous / "frozen_plan.json", v4 / "frozen_plan.json",
              v4 / "VOL/candidate.joblib", v4 / "PLU/candidate.joblib"]
    plan = {"generation_id": GENERATION, "source_hashes": {str(p): sha256(p) for p in source},
            "input_hashes": {str(p): sha256(p) for p in inputs}, "specifications": specs, "protocols": PROTOCOLS,
            "inner_folds": 3, "inner_seed": "outer partition seed + 10000 + outer fold index",
            "estimator_random_seed": 42, "final_selection": "Five grouped folds, seed 42, on development only",
            "criterion": "Pooled OOF macro F1, MCC, accuracy, fewer features, fixed candidate order",
            "scope": "Oxides and Verma combined_contextual; profile/family scope chosen after v4, exploratory",
            "historical_holdout": "Already inspected; excluded from all selection; included only in final refit",
            "geographic": "Fixed oxide-only variants, 3 two-degree-cell folds, replicate-linked cells merged",
            "uncertainty": "Mean, range and SD across three partition seeds; not independent confidence intervals",
            "calibration": "No calibrated probability claim; SVM probability=False",
            "automatic_promotion": False, "cipw_contract": old_plan["cipw"],
            "dependencies": {name: version(name) for name in ("numpy", "pandas", "scipy", "scikit-learn", "xgboost",
                                                            "joblib", "geonormpy", "catboost", "graphviz", "plotly")},
            "git_commit": os.popen("git rev-parse HEAD").read().strip(),
            "git_status": os.popen("git status --porcelain").read(), "parameters": {}}
    for domain in ("VOL", "PLU"):
        count = data.loc[data["ROCK TYPE"].eq(domain), "ROCK_NAME"].nunique()
        plan["parameters"][domain] = {s["id"]: canonical_parameters(
            estimator_for(s, frames[s["profile"]], count).get_params()
        )
                                      for s in specs}
    path = output / "frozen_plan.json"
    if args.resume:
        frozen = json.loads(path.read_text(encoding="utf-8"))
        for key in ("source_hashes", "input_hashes", "specifications", "protocols", "parameters", "dependencies"):
            if frozen[key] != plan[key]:
                raise ValueError(f"Resume configuration changed: {key}")
    else:
        dump_json(path, plan)
    print("PLAN_FROZEN", GENERATION, len(specs), "configurations per search", flush=True)
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run_domain, d, data, frames, membership, v4, output, specs) for d in ("VOL", "PLU")]
        results = [future.result() for future in futures]
    if not all(sha256(p) == digest for p, digest in originals.items()):
        raise ValueError("Original input changed during experiment")
    dump_json(output / "summary.json", {"generation_id": GENERATION, "complete": True,
                                       "original_files_unchanged": len(originals), "models": results,
                                       "plan_sha256": sha256(path)})
    print("STABILITY_COMPLETE", output, flush=True)


if __name__ == "__main__":
    main()
