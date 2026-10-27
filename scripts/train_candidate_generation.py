"""Build isolated candidate bundles with nested grouped model selection.

Production models and the source dataset are never overwritten. The historical
holdout is descriptive only, not a fresh independent test or selection input.
"""

import argparse
import json
import platform
from copy import deepcopy
from importlib.metadata import version
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.preprocessing import LabelEncoder

from geonormml.config import ARTIFACTS_DIR, get_dataset_path
from geonormml.data import load_training_dataset
from geonormml.features import CIPW_FEATURES
from geonormml.generation import (
    GENERATION_ID,
    INPUT_KEYS,
    MAJORS,
    PLAN,
    PROFILES,
    columns_for,
    dump_json,
    result_metrics,
    select_candidate,
    sha256,
    template_for,
)
from geonormml.quality import sample_groups
from geonormml.split import grouped_cv_indices


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    from geonormpy import __version__, available_profiles, cipw

    if __version__ != PLAN["cipw"]["required_engine_version"]:
        raise ValueError("The frozen plan requires GeoNormPy 1.1.0")
    sources = {
        str(p): sha256(p)
        for directory in (get_dataset_path().parents[2], ARTIFACTS_DIR)
        for p in directory.rglob("*")
        if p.is_file()
    }
    plan = deepcopy(PLAN)
    plan.update(
        engine_profiles=available_profiles(),
        python=platform.python_version(),
        dataset_sha256=sha256(get_dataset_path()),
        runner_sha256=sha256(__file__),
        selector_sha256=sha256(Path(__file__).resolve().parents[1] / "src/geonormml/generation.py"),
        dependencies={
            name: version(name) for name in ("numpy", "pandas", "scikit-learn", "xgboost", "joblib", "geonormpy")
        },
    )
    dump_json(output / "frozen_plan.json", plan)
    data = load_training_dataset()
    data["Sample_Group"] = sample_groups(data).to_numpy()
    data = data.set_index("ID_Final", drop=False)
    split = json.loads((ARTIFACTS_DIR / "splits/holdout_split.json").read_text(encoding="utf-8"))
    train_ids, test_ids = set(split["train_ids"]), set(split["test_ids"])
    if train_ids & test_ids or train_ids | test_ids != set(data.index):
        raise ValueError("Recorded split does not partition every original ID")
    frames = {None: data.copy()}
    status_frames = {}
    for profile in PROFILES:
        transformed, statuses = data.copy(), []
        transformed[list(CIPW_FEATURES)] = np.nan
        for sample_id, row in data.iterrows():
            entry = {"ID_Final": int(sample_id), "status": "missing_major", "complete": False}
            if row[list(MAJORS)].notna().all():
                inputs = {key: float(row[key]) for key in INPUT_KEYS if key in row and pd.notna(row[key])}
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
                    complete = bool(result["flags"]["calculation_complete"])
                    entry.update(
                        status="complete" if complete else "incomplete",
                        complete=complete,
                        metadata=json.dumps(result["calculation_metadata"], sort_keys=True),
                        free_components=json.dumps(result.get("free_components_wtpercent", {}), sort_keys=True),
                        mass_error=float(result["mass_balance_error"]),
                    )
                    entry.update({"phase_" + key: float(value) for key, value in result["minerals_wtpercent"].items()})
                    if complete:
                        for column in CIPW_FEATURES:
                            transformed.at[sample_id, column] = float(result["minerals_wtpercent"].get(column, 0))
                        transformed.at[sample_id, "Ap"] += float(result["minerals_wtpercent"].get("FAp", 0))
                except Exception as error:
                    entry.update(
                        status="unsupported"
                        if getattr(error, "code", None) == "unsupported_profile_oxide"
                        else "error",
                        error_code=getattr(error, "code", type(error).__name__),
                        error=str(error),
                    )
            statuses.append(entry)
        raw = pd.DataFrame(statuses).set_index("ID_Final", drop=False)
        raw.to_csv(output / f"{profile}_norms.csv", index=False)
        frames[profile], status_frames[profile] = transformed, raw
        print("COVERAGE", profile, raw.status.value_counts().to_dict(), flush=True)
    common = np.logical_and.reduce([status_frames[p].complete.to_numpy() for p in PROFILES])
    membership = data[["ID_Final", "ROCK TYPE", "ROCK_NAME", "Sample_Group"]].copy()
    membership["eligible_common"] = common
    membership["original_training"] = data.index.isin(train_ids)
    membership["original_holdout"] = data.index.isin(test_ids)
    membership.to_csv(output / "population.csv", index=False)
    summary = {
        "generation_id": GENERATION_ID,
        "release_status": PLAN["release_status"],
        "all_rows": len(data),
        "eligible_rows": int(common.sum()),
        "models": [],
        "plan_sha256": sha256(output / "frozen_plan.json"),
    }
    all_oof, split_audit = [], []
    models_dir = output / "models"
    models_dir.mkdir()
    for domain in ("VOL", "PLU"):
        domain_population = data.loc[common & data["ROCK TYPE"].eq(domain)]
        development = domain_population.loc[domain_population.index.isin(train_ids)]
        historical_test = domain_population.loc[domain_population.index.isin(test_ids)]
        if set(development.Sample_Group) & set(historical_test.Sample_Group):
            raise ValueError("Historical split leaks groups")
        encoder = LabelEncoder().fit(development.ROCK_NAME)
        n_classes = len(encoder.classes_)
        if set(encoder.classes_) != set(domain_population.ROCK_NAME):
            raise ValueError("A class is absent from development data")
        target = encoder.transform(development.ROCK_NAME)
        predicted = np.full(len(development), -1, dtype=int)
        selections = []
        for fold, (train, valid) in enumerate(grouped_cv_indices(development, n_splits=PLAN["outer_folds"]), start=1):
            inner = development.iloc[train]
            selected, scores = select_candidate(
                frames,
                inner,
                target[train],
                n_classes,
                PLAN["inner_folds"],
                progress=lambda row: print("INNER", domain, fold, row["id"], round(row["f1_macro"], 5), flush=True),
            )
            frame, columns = frames[selected["profile"]], columns_for(selected)
            fitted = template_for(selected, inner, n_classes).fit(frame.loc[inner.index, columns], target[train])
            predicted[valid] = fitted.predict(frame.loc[development.iloc[valid].index, columns])
            selections.append({"fold": fold, "selected": selected, "inner_scores": scores})
            split_audit.append(
                {
                    "domain": domain,
                    "outer_fold": fold,
                    "train_ids": inner.ID_Final.tolist(),
                    "valid_ids": development.iloc[valid].ID_Final.tolist(),
                }
            )
            for index in valid:
                all_oof.append(
                    {
                        "ID_Final": int(development.iloc[index].ID_Final),
                        "domain": domain,
                        "fold": fold,
                        "actual": str(development.iloc[index].ROCK_NAME),
                        "predicted": str(encoder.classes_[predicted[index]]),
                    }
                )
            dump_json(output / f"{domain}_outer_selections.json", selections)
            print("OUTER", domain, fold, selected["id"], flush=True)
        if (predicted < 0).any():
            raise ValueError("Missing outer OOF prediction")
        selected, final_scores = select_candidate(
            frames,
            development,
            target,
            n_classes,
            PLAN["final_selection_folds"],
            progress=lambda row: print("FINAL_SELECTION", domain, row["id"], round(row["f1_macro"], 5), flush=True),
        )
        columns, transformed = columns_for(selected), frames[selected["profile"]]
        estimator = template_for(selected, development, n_classes)
        diagnostic = clone(estimator).fit(transformed.loc[development.index, columns], target)
        held_predictions = diagnostic.predict(transformed.loc[historical_test.index, columns])
        final = clone(estimator).fit(
            transformed.loc[domain_population.index, columns], encoder.transform(domain_population.ROCK_NAME)
        )
        contract = deepcopy(plan["cipw"]) if selected["profile"] else None
        if contract:
            contract.update(
                profile=selected["profile"],
                profile_version=plan["engine_profiles"]["profiles"][selected["profile"]]["version"],
            )
        metrics = result_metrics(target, predicted, n_classes)
        info = {
            "domain_code": domain,
            "domain_name": "volcanic" if domain == "VOL" else "plutonic",
            "selected": selected,
            "selection_scores": final_scores,
            "validation": {"kind": "nested_group_cv_selection_procedure", "rows": len(development), **metrics},
            "historical_holdout_descriptive": {
                "rows": len(historical_test),
                **result_metrics(encoder.transform(historical_test.ROCK_NAME), held_predictions, n_classes),
            },
            "fit_rows": len(domain_population),
            "cipw_contract": contract,
            "geospatial_predictors": False,
            "transfer_status": "experimental",
            "generation_id": GENERATION_ID,
            "feature_columns": columns,
            "classes": encoder.classes_.tolist(),
        }
        bundle = {
            **info,
            "model_name": selected["model_name"],
            "feature_set": selected["feature_set"],
            "label_encoder": encoder,
            "estimator": final,
            "provenance": {
                "dataset_sha256": plan["dataset_sha256"],
                "plan_sha256": summary["plan_sha256"],
                "dependencies": plan["dependencies"],
            },
        }
        filename = f"{info['domain_name']}__{selected['id']}.joblib"
        joblib.dump(bundle, models_dir / filename)
        info.update(artifact_path="models/" + filename, artifact_sha256=sha256(models_dir / filename))
        summary["models"].append(info)
        dump_json(output / "summary.json", summary)
        print("EXPORTED_CANDIDATE", domain, selected["id"], json.dumps(metrics), flush=True)
    pd.DataFrame(all_oof).to_csv(output / "nested_oof_predictions.csv", index=False)
    dump_json(output / "outer_splits.json", split_audit)
    summary["originals_unchanged"] = all(sha256(p) == digest for p, digest in sources.items())
    if not summary["originals_unchanged"]:
        raise ValueError("An original dataset or model artifact changed")
    summary["complete"] = True
    dump_json(output / "summary.json", summary)
    dump_json(output / "source_hashes.json", sources)
    print("GENERATION_COMPLETE", output, flush=True)


if __name__ == "__main__":
    main()
