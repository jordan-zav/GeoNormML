"""Recompute expanded OOF evidence and refit the incumbent specification as a matched diagnostic."""

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.preprocessing import LabelEncoder

from geonormml.config import ARTIFACTS_DIR
from geonormml.data import load_training_dataset
from geonormml.expanded import best_record, profile_frame, score_arrays
from geonormml.generation import PROFILES, dump_json, sha256
from geonormml.quality import sample_groups


def review(root, previous):
    root, previous = Path(root), Path(previous)
    plan = json.loads((root / "frozen_plan.json").read_text(encoding="utf-8"))
    report = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    assert report["complete"] and report["plan_sha256"] == sha256(root / "frozen_plan.json")
    for name in ("source_hashes", "input_hashes"):
        assert all(sha256(path) == digest for path, digest in plan[name].items())
    originals = json.loads((previous / "source_hashes.json").read_text(encoding="utf-8"))
    assert all(sha256(path) == digest for path, digest in originals.items())
    data = load_training_dataset().set_index("ID_Final", drop=False)
    data["Sample_Group"] = sample_groups(data)
    membership = pd.read_csv(previous / "population.csv").set_index("ID_Final").loc[data.index]
    assert data.Sample_Group.eq(membership.Sample_Group).all()
    frames = {None: data}
    for profile in PROFILES:
        norms = pd.read_csv(previous / f"{profile}_norms.csv").set_index("ID_Final")
        frames[profile] = profile_frame(data, norms)
        eligible = membership.eligible_common
        frame = frames[profile].loc[eligible]
        np.testing.assert_allclose(frame.SUM_QAP, frame.Q + frame.Or + frame.Ab + frame.An)
        with np.errstate(invalid="ignore", divide="ignore"):
            expected = 100 * frame.An / (frame.An + frame.Ab)
        np.testing.assert_allclose(frame["%An en Pl"], expected, equal_nan=True)
    domains = []
    for item in report["models"]:
        domain = item["domain"]
        directory = root / domain
        rows = pd.read_csv(directory / "oof_predictions.csv").set_index("ID_Final")
        expected_ids = set(data.index[membership.eligible_common & membership.original_training
                                          & data["ROCK TYPE"].eq(domain)])
        assert rows.index.is_unique and set(rows.index) == expected_ids
        assert rows.ROCK_NAME.eq(data.loc[rows.index, "ROCK_NAME"]).all()
        encoder = LabelEncoder().fit(rows.ROCK_NAME)
        target, count = encoder.transform(rows.ROCK_NAME), len(encoder.classes_)
        for result in item["results"]:
            scores = score_arrays(target, encoder.transform(rows[result["procedure"]]), count)
            for key, value in scores.items():
                assert np.isclose(value, result[key], rtol=0, atol=1e-12)
        selections = json.loads((directory / "selections.json").read_text(encoding="utf-8"))
        splits = json.loads((directory / "splits.json").read_text(encoding="utf-8"))
        primary_ids = {s["id"] for s in plan["specifications"] if s["scope"] == "transfer_candidate"}
        assert len(selections) == len(splits) == 5
        for selection, split in zip(selections, splits):
            assert set(split["valid_ids"]) == set(rows.index[rows.fold.eq(split["fold"])])
            assert not set(data.loc[split["train_ids"], "Sample_Group"]) & set(
                data.loc[split["valid_ids"], "Sample_Group"]
            )
            assert {r["id"] for r in selection["inner_scores"]} == primary_ids
            assert best_record(selection["inner_scores"])["id"] == selection["winners"]["all_candidates"]
            for inner in split["inner"]:
                assert set(inner["train_ids"]) | set(inner["valid_ids"]) == set(split["train_ids"])
                assert not set(data.loc[inner["train_ids"], "Sample_Group"]) & set(
                    data.loc[inner["valid_ids"], "Sample_Group"]
                )
        assert len(list(directory.glob("inner_*.json"))) == 600
        assert len(list(directory.glob("final_[0-9][0-9][0-9].json"))) == 120
        assert best_record(item["final_selection_scores"])["id"] == item["final_selection"]["id"]
        assert sha256(directory / "candidate.joblib") == item["model_sha256"]
        bundle = joblib.load(directory / "candidate.joblib")
        assert bundle["selected"] == item["final_selection"]
        selected = item["final_selection"]
        frame = frames[selected["profile"]]
        fitted_ids = data.index[membership.eligible_common & data["ROCK TYPE"].eq(domain)]
        assert bundle["fit_rows"] == len(fitted_ids)
        prediction = bundle["estimator"].predict(frame.loc[fitted_ids, selected["columns"]])
        probabilities = bundle["estimator"].predict_proba(frame.loc[fitted_ids, selected["columns"]])
        assert prediction.shape == (len(fitted_ids),)
        assert probabilities.shape == (len(fitted_ids), count)
        np.testing.assert_allclose(probabilities.sum(axis=1), 1, atol=1e-6)
        # A frozen incumbent configuration, refitted on the same outer folds.
        # Its historical CIPW columns have no recorded engine profile; label this diagnostic explicitly.
        legacy_name = {"VOL": "volcanic__combined_core__XGBoost.joblib",
                       "PLU": "plutonic__combined_core__RandomForest.joblib"}[domain]
        incumbent = joblib.load(ARTIFACTS_DIR / "official_models" / legacy_name)
        incumbent_prediction = pd.Series(-1, index=rows.index, dtype=int)
        assert list(incumbent["label_encoder"].classes_) == list(encoder.classes_)
        for split in splits:
            train, valid = split["train_ids"], split["valid_ids"]
            fitted = clone(incumbent["estimator"]).fit(
                data.loc[train, incumbent["feature_columns"]], encoder.transform(data.loc[train, "ROCK_NAME"])
            )
            incumbent_prediction.loc[valid] = fitted.predict(data.loc[valid, incumbent["feature_columns"]])
        assert incumbent_prediction.ge(0).all()
        baseline_scores = score_arrays(target, incumbent_prediction.loc[rows.index].to_numpy(), count)
        public_results = [{key: value for key, value in result.items() if key != "per_class"}
                          for result in item["results"]]
        domains.append({"domain": domain, "rows": len(rows), "selected_for_final_fit": selected,
                        "results": public_results, "comparisons": item["comparisons"],
                        "incumbent_matched_refit": baseline_scores,
                        "incumbent_interpretation": (
                            "Post-run descriptive matched control; historical norm profile unknown."
                        ),
                        "outer_selected_counts": item["outer_selected_counts"], "model_sha256": item["model_sha256"]})
    return {"generation_id": report["generation_id"], "verified_original_files": len(originals),
            "verified_feature_rows": int(membership.eligible_common.sum()), "domains": domains,
            "primary_configurations_per_domain": 120, "spatial_diagnostics_per_domain": 27,
            "primary_run_fit_count_including_dummy": 5112, "additional_incumbent_control_fits": 10,
            "external_validation": False, "production_models_changed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Use a new review evidence file")
    result = review(args.run, args.previous)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    dump_json(args.output, result)
    print(json.dumps({"verified_original_files": result["verified_original_files"],
                      "domains": [{"domain": d["domain"], "incumbent": d["incumbent_matched_refit"]}
                                  for d in result["domains"]]}))


if __name__ == "__main__":
    main()
