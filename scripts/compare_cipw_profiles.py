"""Compare versioned CIPW profiles without changing official data or deployed models.

Existing trained estimators are cloned and fitted only within the recorded split.
Outputs are research artifacts; this script never publishes or replaces a model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

PROFILES = ("extended_cipw_v3", "verma2003", "pruseth2009")
CORE = ("SiO2", "TiO2", "Al2O3", "FeOT", "CaO", "MgO", "MnO", "Na2O", "K2O", "P2O5")
INPUTS = (*CORE, "CO2", "F", "Cl", "SO3", "S", "ZrO2", "Cr2O3")
MODEL_FILES = {"VOL": "volcanic__combined_core__XGBoost.joblib", "PLU": "plutonic__combined_core__RandomForest.joblib"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def calculation_error_status(error):
    """Keep profile applicability separate from unexpected calculation errors."""
    return (
        "unsupported"
        if getattr(error, "code", None) in {"unsupported_component", "unsupported_profile_oxide"}
        else "error"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine-source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cv-folds", type=int, default=5)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if output.exists():
        raise ValueError("Use a new output directory to preserve earlier evidence.")
    output.mkdir(parents=True)
    sys.path.insert(0, str(args.engine_source.resolve()))
    import geonormpy
    import joblib
    import numpy as np
    import pandas as pd
    from geonormpy import available_profiles, cipw
    from sklearn.base import clone
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, matthews_corrcoef
    from sklearn.model_selection import StratifiedGroupKFold
    from sklearn.pipeline import Pipeline

    if not Path(geonormpy.__file__).resolve().is_relative_to(args.engine_source.resolve()):
        raise ValueError("Wrong GeoNormPy import; isolation failed.")
    if not all(name in available_profiles()["profiles"] for name in PROFILES):
        raise ValueError("The requested three profiles are not available.")
    dataset = root / "Dataset/Filtered/final/GeoNormML_training_curated.xlsx"
    transfer = root / "artifacts/petropyqapf_transfer"
    split_file = root / "artifacts/splits/holdout_split.json"
    source_paths = [
        dataset,
        split_file,
        root / "artifacts/validation/baseline_validation.json",
        transfer / "schemas/official_model_bundle.json",
        *(transfer / "models" / name for name in MODEL_FILES.values()),
    ]
    originals = {str(path): digest(path) for path in source_paths}
    data = pd.read_excel(dataset)
    if len(data) != 2755 or data.ID_Final.nunique() != 2755:
        raise ValueError("Expected all 2755 unique curated IDs.")
    schema = json.loads((transfer / "schemas/official_model_bundle.json").read_text(encoding="utf-8-sig"))
    if digest(dataset) != schema["provenance"]["dataset_sha256"]:
        raise ValueError("Dataset differs from the model reference.")
    split = json.loads(split_file.read_text(encoding="utf-8"))
    train_mask = data.ID_Final.isin(split["train_ids"])
    test_mask = data.ID_Final.isin(split["test_ids"])
    if (train_mask & test_mask).any() or not (train_mask | test_mask).all():
        raise ValueError("Split does not partition all curated IDs.")
    if set(data.loc[train_mask, "Sample_Group"]) & set(data.loc[test_mask, "Sample_Group"]):
        raise ValueError("Sample-group leakage in recorded holdout.")
    bundles = {domain: joblib.load(transfer / "models" / name) for domain, name in MODEL_FILES.items()}
    phases = [key for key in bundles["VOL"]["feature_columns"] if key not in (*CORE, "LOI", "Sum_Oxs")]
    report = {
        "engine_version": geonormpy.__version__,
        "engine_commit": subprocess.check_output(["git", "-C", str(args.engine_source), "rev-parse", "HEAD"])
        .decode()
        .strip(),
        "rows": len(data),
        "dataset_sha256": digest(dataset),
        "profiles": available_profiles(),
        "parameters": {
            "iron_policy": "fixed",
            "fe3_fraction": 0.15,
            "carbonate_mode": "calcite",
            "strict": False,
            "mass_tol": 1e-6,
            "missing_core": "unavailable, not zero",
            "optional_missing": "omitted; default engine conventions apply",
            "input_basis": "reported wt%; no LOI supplied as oxide; same inputs for all profiles",
            "ml_apatite_feature": "Ap=Ap+FAp, explicitly harmonized total apatite group; raw phases preserved",
            "other_ml_features": "fixed original 39-column contract; new phases/free components not added",
            "imputation": ("Training-fold median for missing model features, including LOI; no raw assay rewrite"),
        },
        "norms": {},
        "primary_evaluation": [],
        "historical_replication": [],
        "old_model_sensitivity": [],
        "source_hashes_before": originals,
    }
    predicted_frames = {}
    statuses = {}
    all_norms = {}
    core_present = data[list(CORE)].notna().all(axis=1)
    if any((data.loc[core_present, list(CORE)] < 0).any(axis=1)):
        raise ValueError("Negative required chemistry in source.")
    for profile in PROFILES:
        rows = []
        ml_frame = data.copy()
        ml_frame[phases] = ml_frame[phases].astype(float)
        ml_frame.loc[:, phases] = np.nan
        for index, row in data.iterrows():
            entry = {
                "ID_Final": int(row.ID_Final),
                "domain": row["ROCK TYPE"],
                "status": "missing_major",
                "complete": False,
                "mass_error": None,
                "free_components": "{}",
                "error": None,
            }
            if core_present.iloc[index]:
                inputs = {key: float(row[key]) for key in INPUTS if key in row and pd.notna(row[key])}
                try:
                    result = cipw(
                        inputs,
                        profile=profile,
                        iron_policy="fixed",
                        fe3_fraction=0.15,
                        carbonate_mode="calcite",
                        strict=False,
                        mass_tol=1e-6,
                        debug=True,
                    )
                    entry.update(
                        status="complete" if result["flags"]["calculation_complete"] else "incomplete",
                        complete=bool(result["flags"]["calculation_complete"]),
                        mass_error=float(result["mass_balance_error"]),
                        free_components=json.dumps(result.get("free_components_wtpercent", {}), sort_keys=True),
                        residual_oxides=json.dumps(result.get("residual_oxides_wt", {}), sort_keys=True),
                        calculation_metadata=json.dumps(result["calculation_metadata"], sort_keys=True),
                    )
                    for key, value in result["minerals_wtpercent"].items():
                        entry["phase_" + key] = float(value)
                    if entry["complete"]:
                        for phase in phases:
                            ml_frame.at[index, phase] = float(result["minerals_wtpercent"].get(phase, 0))
                        ml_frame.at[index, "Ap"] = float(result["minerals_wtpercent"].get("Ap", 0)) + float(
                            result["minerals_wtpercent"].get("FAp", 0)
                        )
                except Exception as error:
                    entry.update(
                        status=calculation_error_status(error),
                        error=str(error),
                        error_code=getattr(error, "code", type(error).__name__),
                    )
            rows.append(entry)
        frame = pd.DataFrame(rows)
        frame.to_csv(output / (profile + "_norms.csv"), index=False, encoding="utf-8-sig")
        statuses[profile] = frame.complete.to_numpy(dtype=bool)
        all_norms[profile] = frame
        predicted_frames[profile] = ml_frame
        complete_errors = frame.loc[frame.complete, "mass_error"]
        report["norms"][profile] = {
            "status_counts": {str(k): int(v) for k, v in frame.status.value_counts().items()},
            "max_mass_error_complete": float(complete_errors.max()) if len(complete_errors) else None,
            "median_mass_error_complete": float(complete_errors.median()) if len(complete_errors) else None,
            "error_codes": {
                str(k): int(v) for k, v in frame.get("error_code", pd.Series(dtype=str)).value_counts().items()
            },
        }
        print("NORMS", profile, json.dumps(report["norms"][profile]), flush=True)
        write_json(output / "summary.json", report)
    common = np.logical_and.reduce(list(statuses.values()))
    report["common_complete_rows"] = int(common.sum())
    membership = data[["ID_Final", "ROCK TYPE", "Sample_Group"]].copy()
    membership["train"] = train_mask
    membership["test"] = test_mask
    membership["common_complete"] = common
    membership.to_csv(output / "evaluation_population.csv", index=False, encoding="utf-8-sig")
    # Preserve the original recorded split. Filtering here is an experimental
    # common population only; no curated record is deleted or relabelled.
    predictions = []
    for domain, bundle in bundles.items():
        domain_mask = data["ROCK TYPE"] == domain
        columns = list(bundle["feature_columns"])
        encoder = bundle["label_encoder"]
        labels = list(encoder.classes_)
        template = bundle["estimator"]

        def scores(actual, predicted):
            return {
                "accuracy": float(accuracy_score(actual, predicted)),
                "f1_macro": float(f1_score(actual, predicted, labels=labels, average="macro", zero_division=0)),
                "mcc": float(matthews_corrcoef(actual, predicted)),
            }

        # Reproduce historical holdout properly: never evaluate the deployed
        # final estimator which was refitted on all curated observations.
        old_train = data.loc[domain_mask & train_mask]
        old_test = data.loc[domain_mask & test_mask]
        replicate = clone(template)
        replicate.fit(old_train[columns], encoder.transform(old_train.ROCK_NAME))
        old_pred = encoder.inverse_transform(replicate.predict(old_test[columns]))
        report["historical_replication"].append(
            {"domain": domain, "train": len(old_train), "test": len(old_test), **scores(old_test.ROCK_NAME, old_pred)}
        )
        print("REPLICATE", domain, json.dumps(report["historical_replication"][-1]), flush=True)
        # Frozen-model sensitivity is diagnostic only; not validation accuracy.
        sensitivity_mask = domain_mask & common
        original_probability = template.predict_proba(data.loc[sensitivity_mask, columns])
        for profile, frame in predicted_frames.items():
            probability = template.predict_proba(frame.loc[sensitivity_mask, columns])
            report["old_model_sensitivity"].append(
                {
                    "domain": domain,
                    "profile": profile,
                    "rows": int(sensitivity_mask.sum()),
                    "changed_top_class": int(
                        np.sum(np.argmax(probability, axis=1) != np.argmax(original_probability, axis=1))
                    ),
                    "changed_probability_gt_1e_6": int(
                        np.sum(np.max(abs(probability - original_probability), axis=1) > 1e-6)
                    ),
                    "max_probability_delta": float(np.max(abs(probability - original_probability))),
                }
            )
        selected = domain_mask & common
        train_idx = np.flatnonzero((selected & train_mask).to_numpy())
        test_idx = np.flatnonzero((selected & test_mask).to_numpy())
        train = data.iloc[train_idx]
        group_counts = train.groupby("ROCK_NAME").Sample_Group.nunique()
        folds_count = min(args.cv_folds, int(group_counts.min()))
        if folds_count < 2:
            raise ValueError("Insufficient groups for common-population CV.")
        cv = list(
            StratifiedGroupKFold(n_splits=folds_count, shuffle=True, random_state=42).split(
                train, train.ROCK_NAME, train.Sample_Group
            )
        )
        report.setdefault("common_population", {})[domain] = {
            "rows": int(selected.sum()),
            "train": len(train_idx),
            "test": len(test_idx),
            "cv_folds": folds_count,
            "train_groups": int(train.Sample_Group.nunique()),
            "test_groups": int(data.iloc[test_idx].Sample_Group.nunique()),
        }
        for a, b in cv:
            if set(train.iloc[a].Sample_Group) & set(train.iloc[b].Sample_Group):
                raise ValueError("CV leakage")
        scenarios = {"stored_reference": data, "oxides_only_control": data, **predicted_frames}
        for scenario, frame in scenarios.items():
            if scenario == "oxides_only_control":
                cols = [key for key in columns if key not in phases]
                last_name, last_model = template.steps[-1]
                model_template = Pipeline(
                    [
                        (
                            "preprocessor",
                            ColumnTransformer(
                                [("numeric", SimpleImputer(strategy="median", keep_empty_features=True), cols)]
                            ),
                        ),
                        (last_name, clone(last_model)),
                    ]
                )
            else:
                cols = columns
                model_template = template
            cv_scores = []
            for fold, (a, b) in enumerate(cv, 1):
                model = clone(model_template)
                model.fit(frame.iloc[train_idx[a]][cols], encoder.transform(data.iloc[train_idx[a]].ROCK_NAME))
                result = encoder.inverse_transform(model.predict(frame.iloc[train_idx[b]][cols]))
                cv_scores.append(scores(data.iloc[train_idx[b]].ROCK_NAME, result))
                print("CV", domain, scenario, fold, flush=True)
            model = clone(model_template)
            model.fit(frame.iloc[train_idx][cols], encoder.transform(data.iloc[train_idx].ROCK_NAME))
            test_predictions = encoder.inverse_transform(model.predict(frame.iloc[test_idx][cols]))
            entry = {
                "domain": domain,
                "scenario": scenario,
                "train": len(train_idx),
                "test": len(test_idx),
                "cv_folds": folds_count,
                "holdout": scores(data.iloc[test_idx].ROCK_NAME, test_predictions),
                "cv_mean": {key: float(np.mean([row[key] for row in cv_scores])) for key in cv_scores[0]},
                "cv_std": {key: float(np.std([row[key] for row in cv_scores], ddof=1)) for key in cv_scores[0]},
                "cv_scores": cv_scores,
            }
            report["primary_evaluation"].append(entry)
            cm = pd.DataFrame(
                confusion_matrix(data.iloc[test_idx].ROCK_NAME, test_predictions, labels=labels),
                index=labels,
                columns=labels,
            )
            cm.to_csv(output / (domain + "_" + scenario + "_confusion.csv"), encoding="utf-8-sig")
            predictions.extend(
                {
                    "ID_Final": int(data.iloc[i].ID_Final),
                    "group": str(data.iloc[i].Sample_Group),
                    "domain": domain,
                    "scenario": scenario,
                    "actual": data.iloc[i].ROCK_NAME,
                    "predicted": str(pred),
                }
                for i, pred in zip(test_idx, test_predictions)
            )
            print("HOLDOUT", domain, scenario, json.dumps(entry["holdout"]), flush=True)
            write_json(output / "summary.json", report)
    pd.DataFrame(predictions).to_csv(output / "holdout_predictions.csv", index=False, encoding="utf-8-sig")
    report["source_hashes_after"] = {str(path): digest(path) for path in source_paths}
    if report["source_hashes_after"] != originals:
        raise ValueError("An original artifact changed during audit.")
    report["originals_unchanged"] = True
    # Paired group bootstrap on the same held-out sample groups. The historical
    # holdout has been used before; intervals are descriptive, not fresh external validation.
    table = pd.DataFrame(predictions)
    rng = np.random.default_rng(20261026)
    report["paired_accuracy_differences"] = []
    for domain in MODEL_FILES:
        subset = table[table.domain == domain]
        wide = subset.pivot(index=["ID_Final", "group", "actual"], columns="scenario", values="predicted").reset_index()
        groups = wide["group"].unique()
        for scenario in PROFILES:
            correct_new = (wide[scenario] == wide.actual).to_numpy(dtype=float)
            correct_old = (wide.stored_reference == wide.actual).to_numpy(dtype=float)
            difference = correct_new - correct_old
            sums = np.array([difference[wide["group"] == group].sum() for group in groups])
            counts = np.array([(wide["group"] == group).sum() for group in groups])
            sampled = rng.integers(0, len(groups), size=(2000, len(groups)))
            estimates = sums[sampled].sum(axis=1) / counts[sampled].sum(axis=1)
            low, high = np.quantile(estimates, [0.025, 0.975])
            report["paired_accuracy_differences"].append(
                {
                    "domain": domain,
                    "profile": scenario,
                    "difference_percentage_points": float(100 * difference.mean()),
                    "descriptive_95pct_group_bootstrap_pp": [float(100 * low), float(100 * high)],
                    "improved_samples": int(np.sum(difference > 0)),
                    "worsened_samples": int(np.sum(difference < 0)),
                }
            )
    report["complete"] = True
    write_json(output / "summary.json", report)
    print(
        "COMPLETE",
        json.dumps({"output": str(output), "rows": len(data), "common": int(common.sum()), "models_saved": False}),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
