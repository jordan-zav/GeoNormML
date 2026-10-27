"""Independent score audit, matched geographic controls and explicitly post-hoc family candidates."""

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, matthews_corrcoef, recall_score
from sklearn.preprocessing import LabelEncoder

from geonormml.data import load_training_dataset
from geonormml.expanded import best_record, profile_frame, score_arrays
from geonormml.generation import dump_json, sha256
from geonormml.quality import sample_groups
from geonormml.stability import ALGORITHMS, fit_model, geography_groups, predict_encoded, seeded_folds


def verify_metrics(actual, predicted, labels, record):
    actual, predicted = np.asarray(actual), np.asarray(predicted)
    recall = recall_score(actual, predicted, labels=labels, average=None, zero_division=0)
    support = np.array([np.sum(actual == label) for label in labels])
    recomputed = {"accuracy": accuracy_score(actual, predicted),
                  "f1_macro": f1_score(actual, predicted, labels=labels, average="macro", zero_division=0),
                  "mcc": matthews_corrcoef(actual, predicted),
                  "balanced_accuracy": float(recall[support > 0].mean())}
    for key, value in recomputed.items():
        if not np.isclose(value, record[key], rtol=0, atol=1e-12):
            raise ValueError(f"Saved {key} does not match independent sklearn calculation")
    return {key: float(value) for key, value in recomputed.items()}


def verify_splits(data, universe, saved, expected):
    seen = []
    if len(saved) != len(expected):
        raise ValueError("Unexpected number of folds")
    for recorded, (train, valid) in zip(saved, expected):
        train_ids, valid_ids = list(universe.iloc[train].index), list(universe.iloc[valid].index)
        if recorded["train_ids"] != train_ids or recorded["valid_ids"] != valid_ids:
            raise ValueError("Stored split cannot be reproduced from its seed")
        if set(data.loc[train_ids, "Sample_Group"]) & set(data.loc[valid_ids, "Sample_Group"]):
            raise ValueError("Replicate leakage")
        seen.extend(valid_ids)
    if len(seen) != len(universe) or set(seen) != set(universe.index):
        raise ValueError("OOF does not cover every development row exactly once")


def verify_search(directory, population, encoder, specs, folds):
    saved = json.loads((directory / "splits.json").read_text(encoding="utf-8"))
    verify_splits(population, population, saved, folds)
    paths = sorted(directory.glob("candidate_[0-9][0-9][0-9].json"))
    if len(paths) != len(specs):
        raise ValueError("Incomplete candidate search")
    records = []
    for path, spec in zip(paths, specs):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record["id"] != spec["id"] or len(record["predictions"]) != len(population):
            raise ValueError("Candidate OOF identity mismatch")
        labels = encoder.inverse_transform(np.asarray(record["predictions"], dtype=int))
        verify_metrics(population.ROCK_NAME, labels, encoder.classes_, record)
        records.append({key: value for key, value in record.items() if key != "predictions"})
    return records


def plot_results(reports, output):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = [*ALGORITHMS, "incumbent_historical", "v4_frozen_refit"]
    labels = ["RandomForest", "XGBoost", "SVM", "ExtraTrees", "HistGradientBoosting", "CatBoost",
              "Regresión logística", "Control histórico*", "Control v4*"]
    figure, axes = plt.subplots(1, 2, figsize=(12, 6), sharey=True)
    for axis, report in zip(axes, reports):
        rows = {row["procedure"]: row for row in report["aggregate"]}
        best = max(ALGORITHMS, key=lambda name: rows[name]["f1_macro"]["mean"])
        for index, name in enumerate(names):
            metric = rows[name]["f1_macro"]
            color = "#711610" if name == best else "#24527a" if name in ALGORITHMS else "#777777"
            axis.errorbar(metric["mean"], index, xerr=metric["sd_across_partitions"], fmt="o", color=color,
                          capsize=3, markersize=5)
            axis.annotate(f"{metric['mean']:.3f}", (metric["mean"], index), xytext=(9, -3),
                          textcoords="offset points", fontsize=9)
        axis.set_xlim(0.2, 0.8)
        axis.set_xlabel("Macro F1: media ± desviación entre repartos")
        domain_label = "Volcánicas" if report["domain"] == "VOL" else "Plutónicas"
        axis.set_title(f"{domain_label} · n={report['development_rows']}")
        axis.grid(axis="x", color="#dddddd", linewidth=0.6)
        axis.set_yticks(range(len(labels)), labels)
    axes[0].invert_yaxis()
    figure.suptitle("Validación anidada por grupos · 3 semillas · 5 folds externos / 3 internos", fontsize=12)
    figure.text(0.5, 0.015, ("Desviaciones descriptivas, no intervalos de confianza. "
                            "*Controles históricos, sin prueba externa nueva."),
                ha="center", fontsize=9)
    figure.tight_layout(rect=(0, 0.05, 1, 0.94))
    figure.savefig(output / "stability_macro_f1.png", dpi=180)
    figure.savefig(output / "stability_macro_f1.svg")
    plt.close(figure)


def review(root, previous, output):
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    plan = json.loads((root / "frozen_plan.json").read_text(encoding="utf-8"))
    if not summary["complete"] or summary["plan_sha256"] != sha256(root / "frozen_plan.json"):
        raise ValueError("Main experiment is incomplete or plan changed")
    for name in ("source_hashes", "input_hashes"):
        if not all(sha256(path) == digest for path, digest in plan[name].items()):
            raise ValueError(f"Frozen {name} changed")
    originals = json.loads((previous / "source_hashes.json").read_text(encoding="utf-8"))
    if not all(sha256(path) == digest for path, digest in originals.items()):
        raise ValueError("Original artifacts changed")
    # Freeze the added diagnostic before fitting matched controls or post-hoc candidates.
    dump_json(output / "review_plan.json", {
        "main_plan_sha256": summary["plan_sha256"], "reviewer_sha256": sha256(__file__),
        "matched_control": ("Exactly each geographic fixed oxide spec; 3 replicate-group folds, "
                            "seed42, same coordinate coverage"),
        "family_candidate": ("Highest mean nested OOF macro F1 across 3 five-fold seeds; "
                             "then best final-CV spec within family"),
        "status": "Post-run exploratory family choice, never automatic promotion or fresh external validation",
    })
    data = load_training_dataset().set_index("ID_Final", drop=False)
    data["Sample_Group"] = sample_groups(data)
    membership = pd.read_csv(previous / "population.csv").set_index("ID_Final").loc[data.index]
    if not membership.Sample_Group.eq(data.Sample_Group).all():
        raise ValueError("Group identity changed")
    norms = pd.read_csv(previous / "verma2003_norms.csv").set_index("ID_Final")
    frames = {None: data, "verma2003": profile_frame(data, norms)}
    specs = plan["specifications"]
    by_id = {spec["id"]: spec for spec in specs}
    reports = []
    for result in summary["models"]:
        domain = result["domain"]
        directory = root / domain
        eligible = data.loc[membership.eligible_common & data["ROCK TYPE"].eq(domain)]
        development = eligible.loc[membership.loc[eligible.index, "original_training"]]
        encoder = LabelEncoder().fit(development.ROCK_NAME)
        for protocol in result["protocols"]:
            path = directory / protocol["id"]
            if (protocol["plan_sha256"] != summary["plan_sha256"]
                    or protocol["oof_sha256"] != sha256(path / "oof_predictions.csv")):
                raise ValueError("Protocol checksum failed")
            table = pd.read_csv(path / "oof_predictions.csv").set_index("ID_Final")
            if list(table.index) != list(development.index) or not table.ROCK_NAME.eq(development.ROCK_NAME).all():
                raise ValueError("Unexpected protocol population or target")
            splits = json.loads((path / "splits.json").read_text(encoding="utf-8"))
            selections = json.loads((path / "selections.json").read_text(encoding="utf-8"))
            expected = seeded_folds(development, protocol["outer_folds"], protocol["seed"])
            verify_splits(data, development, splits, expected)
            for split, selection in zip(splits, selections):
                inner = development.loc[split["train_ids"]]
                fold = split["fold"]
                records = verify_search(path / f"outer_{fold}", inner, encoder, specs,
                                        seeded_folds(inner, 3, protocol["seed"] + 10000 + fold))
                for name, selected_id in selection["winners"].items():
                    candidates = records if name == "all_candidates" else [r for r in records if r["algorithm"] == name]
                    if best_record(candidates)["id"] != selected_id:
                        raise ValueError("Saved selection violates ranking rule")
                if set(table.index[table.fold.eq(fold)]) != set(split["valid_ids"]):
                    raise ValueError("Predictions assigned to wrong external fold")
            for metric in protocol["results"]:
                verify_metrics(table.ROCK_NAME, table[metric["procedure"]], encoder.classes_, metric)
        for aggregate in result["aggregate"]:
            repeated = [next(r for r in p["results"] if r["procedure"] == aggregate["procedure"])
                        for p in result["protocols"] if p["outer_folds"] == 5]
            for metric in ("accuracy", "f1_macro", "mcc"):
                values = [r[metric] for r in repeated]
                expected = {"mean": np.mean(values), "sd_across_partitions": np.std(values, ddof=1),
                            "min": min(values), "max": max(values)}
                if any(not np.isclose(value, aggregate[metric][key], rtol=0, atol=1e-12)
                       for key, value in expected.items()):
                    raise ValueError("Partition aggregate does not reproduce")
        final = verify_search(directory / "final_selection", development, encoder, specs,
                              seeded_folds(development, 5, 42))
        if best_record(final)["id"] != result["final_selected"]["id"]:
            raise ValueError("Final candidate selection mismatch")
        model_path = directory / "candidate.joblib"
        if sha256(model_path) != result["model_sha256"]:
            raise ValueError("Final weight checksum mismatch")
        bundle = joblib.load(model_path)
        selected = bundle["selected"]
        if bundle["fit_rows"] != len(eligible) or bundle["plan_sha256"] != summary["plan_sha256"]:
            raise ValueError("Final weight provenance mismatch")
        frame = frames[selected["profile"]].loc[eligible.index, selected["columns"]]
        prediction = predict_encoded(bundle["estimator"], frame)
        if len(prediction) != len(eligible) or not set(prediction) <= set(range(len(encoder.classes_))):
            raise ValueError("Final weight inference failed")
        if hasattr(bundle["estimator"], "predict_proba"):
            np.testing.assert_allclose(bundle["estimator"].predict_proba(frame).sum(axis=1), 1, atol=1e-6)
        geometry = result["geographic_diagnostic"]
        matched = []
        unseen = []
        if geometry["status"] == "complete":
            table = pd.read_csv(directory / "geographic_oof.csv").set_index("ID_Final")
            groups = geography_groups(development)
            if set(table.index) != set(groups.index) or not table.geographic_group.eq(groups.loc[table.index]).all():
                raise ValueError("Geographic population or blocks changed")
            splits = json.loads((directory / "geographic_splits.json").read_text(encoding="utf-8"))
            for split in splits:
                train, valid = split["train_ids"], split["valid_ids"]
                if set(groups.loc[train]) & set(groups.loc[valid]) or set(data.loc[train, "Sample_Group"]) & set(
                    data.loc[valid, "Sample_Group"]
                ):
                    raise ValueError("Geographic leakage")
                absent = set(data.loc[valid, "ROCK_NAME"]) - set(data.loc[train, "ROCK_NAME"])
                unseen.append({"fold": split["fold"], "unseen_classes": sorted(absent),
                               "unseen_rows": int(data.loc[valid, "ROCK_NAME"].isin(absent).sum()),
                               "train_rows": len(train), "valid_rows": len(valid)})
            for metric in geometry["results"]:
                verify_metrics(table.ROCK_NAME, table[metric["algorithm"]], encoder.classes_, metric)
            population = development.loc[table.index]
            control_encoder = LabelEncoder().fit(population.ROCK_NAME)
            control_target = control_encoder.transform(population.ROCK_NAME)
            controls = seeded_folds(population, 3, 42)
            for algorithm, spec in geometry["fixed_specs"].items():
                predicted = np.full(len(population), -1, dtype=int)
                for train, valid in controls:
                    fitted = fit_model(spec, frames[None].loc[population.iloc[train].index],
                                       control_target[train], len(control_encoder.classes_))
                    predicted[valid] = predict_encoded(
                        fitted, frames[None].loc[population.iloc[valid].index, spec["columns"]]
                    )
                labels = control_encoder.inverse_transform(predicted)
                score = score_arrays(encoder.transform(population.ROCK_NAME), encoder.transform(labels),
                                     len(encoder.classes_))
                matched.append({"algorithm": algorithm, **score})
                print("MATCHED_GEO_CONTROL", domain, algorithm, flush=True)
        ranking = sorted([r for r in result["aggregate"] if r["procedure"] in ALGORITHMS],
                         key=lambda r: (-r["f1_macro"]["mean"], -r["mcc"]["mean"], -r["accuracy"]["mean"]))
        family = ranking[0]["procedure"]
        family_spec = by_id[best_record([r for r in final if r["algorithm"] == family])["id"]]
        family_model = fit_model(family_spec, frames[family_spec["profile"]].loc[eligible.index],
                                 encoder.transform(eligible.ROCK_NAME), len(encoder.classes_))
        candidate_path = output / f"{domain}__{family}__posthoc_candidate.joblib"
        joblib.dump({"generation_id": summary["generation_id"], "selected": family_spec, "estimator": family_model,
                     "label_encoder": encoder, "fit_rows": len(eligible),
                     "status": "posthoc_candidate_external_pending",
                     "main_plan_sha256": summary["plan_sha256"]}, candidate_path)
        reports.append({"domain": domain, "development_rows": len(development), "fit_rows": len(eligible),
                        "aggregate": result["aggregate"], "protocols": result["protocols"],
                        "prespecified_final_candidate": result["final_selected"],
                        "posthoc_top_family": family, "posthoc_family_candidate": family_spec,
                        "posthoc_candidate_sha256": sha256(candidate_path),
                        "geographic_diagnostic": geometry, "matched_replicate3_controls": matched,
                        "geographic_fold_coverage": unseen})
    plot_results(reports, output)
    return {"generation_id": summary["generation_id"], "verified_original_files": len(originals),
            "verified_primary_development_rows": sum(r["development_rows"] for r in reports),
            "original_models_changed": False, "external_validation": False, "domains": reports,
            "extra_matched_control_fits": sum(len(r["matched_replicate3_controls"]) * 3 for r in reports),
            "extra_posthoc_family_fits": len(reports)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    result = review(args.run, args.previous, args.output)
    dump_json(args.output / "review.json", result)
    print("STABILITY_REVIEW_COMPLETE", args.output, flush=True)


if __name__ == "__main__":
    main()
