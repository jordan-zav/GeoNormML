"""Read-only parity audit of a private frozen v5 transfer against an installed SDK.

Outputs, adapter weights and row-level evidence are PRIVATE. Run through the
resource launcher with a trusted transfer and an explicitly new output directory.
No estimator is fitted or selected by this script.
"""

import argparse
import hashlib
import json
import platform
from importlib.metadata import version
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

import geonormml
from geonormml import create_model_manifest, load_model, predict
from geonormml.inference import _prepare_frame

GENERATION = "partition_stability_v5_20261027"
FROZEN_PLAN_HASH = "12c6ce11a2e853ec992edb5967fa3be6409052eb6a631790b04fb5e77ad97e8a"


def digest(path):
    hasher = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def verify_transfer(root):
    document = read_json(root / "transfer_manifest.json")
    assert document["generation_id"] == GENERATION and document["private_transfer_only"]
    hashes = {}
    for entry in document["files"]:
        path = (root / entry["relative_path"]).resolve()
        assert path.is_relative_to(root), entry["relative_path"]
        assert path.stat().st_size == entry["size_bytes"], entry["relative_path"]
        hashes[path] = digest(path)
        assert hashes[path] == entry["sha256"], entry["relative_path"]
    return hashes


def resolve_input(original, transfer, mapping, dataset):
    if original.lower().endswith(".xlsx"):
        return dataset
    relative = mapping.get(original)
    if relative is None:
        return None
    path = (transfer / relative).resolve()
    if not path.is_relative_to(transfer):
        raise ValueError("Input mapping escapes the private transfer")
    return path


def boolean_column(values):
    result = values.astype(str).str.lower().map({"true": True, "false": False})
    if result.isna().any():
        raise ValueError("Unrecognized frozen boolean value")
    return result.astype(bool)


def expected_features(source, norms, columns, domain):
    """Reconstruct from saved normative tables and independently stated category rules."""
    expected = source[columns[:12]].copy()
    if domain == "PLU":
        phases = columns[12:-2]
        raw = norms.reindex(source.index)
        if not boolean_column(raw.complete).all():
            raise ValueError("An eligible reference norm is not complete")
        for phase in phases:
            expected[phase] = raw.get("phase_" + phase, pd.Series(0.0, index=source.index)).fillna(0.0)
        expected["Ap"] += raw.get("phase_FAp", pd.Series(0.0, index=source.index)).fillna(0.0)
        expected["Clase_SiO2"] = np.select(
            [source.SiO2.lt(45), source.SiO2.lt(52), source.SiO2.lt(63)],
            ["Ultramafica", "Basica", "Intermedia"],
            default="Acida",
        )
        alkaline = expected.Ne.ge(1) | expected.Le.ge(1) | (source.SiO2.lt(52) & (source.Na2O + source.K2O).ge(5))
        expected["Serie_Mag"] = np.where(alkaline, "Alcalina", "Subalcalina")
    return expected[columns]


def audit_domain(domain, generation, output, population, data, norms, plan, global_summary):
    directory = generation / domain
    record = read_json(directory / "summary.json")
    path = directory / "candidate.joblib"
    source_hash = digest(path)
    global_record = next(item for item in global_summary["models"] if item["domain"] == domain)
    assert source_hash == record["model_sha256"] == global_record["model_sha256"]
    # Only the owner-supplied, checksum-verified original is deserialized.
    original = joblib.load(path)
    assert original["generation_id"] == GENERATION
    assert original["plan_sha256"] == FROZEN_PLAN_HASH
    assert original["selected"] == record["final_selected"]
    selected = original["selected"]
    expected_id = {
        "VOL": "oxides_core__HistGB__balanced15",
        "PLU": "combined_contextual__RandomForest__reference_leaf3",
    }[domain]
    assert selected["id"] == expected_id
    columns = selected["columns"]
    classes = original["label_encoder"].classes_.tolist()
    eligible = boolean_column(population.eligible_common) & population["ROCK TYPE"].eq(domain)
    ids = population.loc[eligible, "ID_Final"].tolist()
    source = data.loc[ids].copy()
    assert len(ids) == record["fit_rows"] == original["fit_rows"]
    assert source["ROCK TYPE"].eq(domain).all()
    reference = expected_features(source, norms, columns, domain)
    root = output / "adapters" / domain
    root.mkdir(parents=True)
    normative = (
        None
        if domain == "VOL"
        else {
            "engine_version": "1.1.0",
            "profile": "verma2003",
            "profile_version": "1.0",
            "iron_policy": "fixed",
            "fe3_fraction": 0.15,
            "carbonate_mode": "calcite",
            "apatite_feature": "Ap + FAp",
        }
    )
    contract = plan["cipw_contract"]
    assert contract["required_engine_version"] == "1.1.0" and contract["iron_policy"] == "fixed"
    assert contract["fe3_fraction"] == 0.15 and contract["carbonate_mode"] == "calcite"
    metadata = {
        "generation_id": GENERATION,
        "domain_code": domain,
        "feature_set": selected["family"],
        "feature_columns": columns,
        "classes": classes,
        "input_mode": "oxide_chemistry",
        "normative": normative,
        "python_version": ".".join(platform.python_version_tuple()[:2]),
        "dependencies": {
            name: plan["dependencies"][name]
            for name in ("numpy", "scipy", "scikit-learn", "joblib", "xgboost", "pandas")
        },
        "original_training_python_version": None,
        "adapter_serialization_python_version": platform.python_version(),
        "provenance": {
            "source_sha256": source_hash,
            "plan_sha256": FROZEN_PLAN_HASH,
            "original_training_python_recorded": False,
            "note": "Original Python unknown; this adapter's current-environment compatibility is tested.",
        },
    }
    artifact = root / "model.joblib"
    adapter = {
        **original,
        "feature_columns": columns,
        "classes": classes,
        "domain_code": domain,
        "input_mode": "oxide_chemistry",
        "feature_set": selected["family"],
        "normative": normative,
        "adapter_provenance": metadata["provenance"],
    }
    # This serializes the same already-fitted estimator with explicit metadata.
    # No fit, clone, parameter change or source-file replacement occurs.
    joblib.dump(adapter, artifact)
    manifest = create_model_manifest(artifact, metadata)
    loaded = load_model(manifest, trusted=True)
    actual_features, errors = _prepare_frame(source, loaded.manifest)
    assert errors.eq("").all(), errors.value_counts().to_dict()
    numeric = columns if domain == "VOL" else columns[:-2]
    expected_array = reference[numeric].to_numpy(dtype=float)
    actual_array = actual_features[numeric].to_numpy(dtype=float)
    np.testing.assert_allclose(actual_array, expected_array, rtol=1e-12, atol=1e-10, equal_nan=True)
    feature_error = float(np.nanmax(np.abs(actual_array - expected_array)))
    if domain == "PLU":
        for column in columns[-2:]:
            assert reference[column].tolist() == actual_features[column].tolist()
    original_probabilities = original["estimator"].predict_proba(reference)
    result = predict(source, loaded, id_column="ID_Final")
    assert result.status.eq("predicted").all()
    actual_probabilities = result[["probability::" + label for label in classes]].to_numpy(dtype=float)
    np.testing.assert_allclose(actual_probabilities, original_probabilities, rtol=1e-12, atol=1e-12)
    expected_labels = original["label_encoder"].inverse_transform(original["estimator"].predict(reference))
    assert result.prediction.tolist() == expected_labels.tolist()
    assert result.sample_id.tolist() == ids
    # Verify the same original estimator via the published prepared-features route.
    prepared_metadata = {
        **metadata,
        "input_mode": "prepared_features",
        "normative": None,
        "categorical_columns": [] if domain == "VOL" else columns[-2:],
    }
    prepared_manifest = create_model_manifest(artifact, prepared_metadata, output=root / "prepared.json")
    prepared = predict(reference, prepared_manifest, trusted=True)
    np.testing.assert_allclose(
        prepared.filter(like="probability::").to_numpy(),
        original_probabilities,
        rtol=1e-12,
        atol=1e-12,
    )
    # Explicit auxiliary-absence and measured-negative-LOI cases use the source
    # estimator and the same frozen norm features as their reference.
    for value in (np.nan, -0.12):
        altered = source.iloc[:3].copy()
        altered["LOI"] = value
        altered["Sum_Oxs"] = np.nan
        baseline = reference.iloc[:3].copy()
        baseline["LOI"] = value
        baseline["Sum_Oxs"] = np.nan
        via_api = predict(altered, loaded).filter(like="probability::").to_numpy()
        np.testing.assert_allclose(via_api, original["estimator"].predict_proba(baseline), rtol=1e-12, atol=1e-12)
    result.to_csv(output / f"{domain}_api_predictions_PRIVATE.csv", index=False)
    return {
        "domain": domain,
        "samples": len(ids),
        "features": len(columns),
        "classes": len(classes),
        "source_sha256": source_hash,
        "adapter_sha256": digest(artifact),
        "max_feature_absolute_difference": feature_error,
        "max_probability_absolute_difference": float(np.max(np.abs(actual_probabilities - original_probabilities))),
        "labels_identical": True,
        "prepared_and_raw_routes_passed": True,
        "optional_auxiliary_tests_passed": True,
        "original_training_python_version": None,
        "interpretation": "Current-environment parity, not external performance or original-Python reconstruction.",
    }


def review_oof(generation, output, data, population, domain):
    records, matrices = [], []
    original = read_json(generation / domain / "summary.json")
    labels = sorted(data.loc[data["ROCK TYPE"].eq(domain), "ROCK_NAME"].unique())
    family = "HistGB" if domain == "VOL" else "RandomForest"
    for protocol in original["protocols"]:
        table = pd.read_csv(generation / domain / protocol["id"] / "oof_predictions.csv")
        assert len(table) == original["development_rows"] and table.ID_Final.is_unique
        assert table.ROCK_NAME.tolist() == data.loc[table.ID_Final, "ROCK_NAME"].tolist()
        assert table.groupby("Sample_Group").fold.nunique().le(1).all()
        for procedure in ("all_candidates", family):
            assert set(table[procedure]).issubset(labels)
            report = classification_report(
                table.ROCK_NAME, table[procedure], labels=labels, output_dict=True, zero_division=0
            )
            saved = next(item for item in protocol["results"] if item["procedure"] == procedure)
            np.testing.assert_allclose(report["macro avg"]["f1-score"], saved["f1_macro"], atol=1e-12)
            for label in labels:
                row = report[label]
                records.append(
                    {
                        "domain": domain,
                        "protocol": protocol["id"],
                        "seed": protocol["seed"],
                        "folds": protocol["outer_folds"],
                        "procedure": procedure,
                        "class": label,
                        "support": int(row["support"]),
                        "precision": row["precision"],
                        "recall": row["recall"],
                        "f1": row["f1-score"],
                    }
                )
            matrices.append(
                {
                    "domain": domain,
                    "protocol": protocol["id"],
                    "procedure": procedure,
                    "labels": labels,
                    "matrix": confusion_matrix(table.ROCK_NAME, table[procedure], labels=labels).tolist(),
                }
            )
    pd.DataFrame(records).to_csv(output / f"{domain}_oof_class_metrics_PRIVATE.csv", index=False)
    write_json(output / f"{domain}_oof_confusions_PRIVATE.json", matrices)
    five = pd.DataFrame(records).query("folds == 5")
    aggregate = (
        five.groupby(["domain", "procedure", "class"], sort=False)
        .agg(
            repeated_partitions=("seed", "nunique"),
            support=("support", "first"),
            mean_recall=("recall", "mean"),
            min_recall=("recall", "min"),
            max_recall=("recall", "max"),
            mean_f1=("f1", "mean"),
            min_f1=("f1", "min"),
            max_f1=("f1", "max"),
        )
        .reset_index()
    )
    aggregate.to_csv(output / f"{domain}_class_stability_PRIVATE.csv", index=False)
    return {
        "domain": domain,
        "development_rows": original["development_rows"],
        "protocols": len(original["protocols"]),
        "selected_family": family,
        "class_review": aggregate.to_dict(orient="records"),
        "probability_calibration": "not_assessable_from_saved_label_only_OOF",
        "interpretation": "Correlated internal selection-procedure repeats, not final-model or external evaluation.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transfer", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    transfer, dataset, output = args.transfer.resolve(), args.dataset.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    hashes = verify_transfer(transfer)
    generation = transfer / "CandidateModels" / GENERATION
    assert digest(generation / "frozen_plan.json") == FROZEN_PLAN_HASH
    plan = read_json(generation / "frozen_plan.json")
    summary = read_json(generation / "summary.json")
    assert summary["complete"] and summary["generation_id"] == GENERATION
    assert summary["plan_sha256"] == FROZEN_PLAN_HASH
    mapping = read_json(transfer / "metadata/path_mapping.json")["original_to_transfer"]
    resolved, unavailable_antecedents = {}, []
    for original, expected_hash in plan["input_hashes"].items():
        path = resolve_input(original, transfer, mapping, dataset)
        if path is None:
            unavailable_antecedents.append({"original_path": original, "recorded_sha256": expected_hash})
            continue
        assert digest(path) == expected_hash, path.name
        resolved[path.name] = path
    assert {dataset.name, "population.csv", "verma2003_norms.csv"}.issubset(resolved)
    hashes[dataset] = digest(dataset)
    for package in ("numpy", "pandas", "scipy", "scikit-learn", "joblib", "xgboost", "geonormpy"):
        assert version(package) == plan["dependencies"][package], package
    assert geonormml.__version__ == version("geonormml") == "0.1.0"
    data = pd.read_excel(dataset).set_index("ID_Final", drop=False)
    assert len(data) == 2755 and data.index.is_unique
    population = pd.read_csv(resolved["population.csv"])
    norms = pd.read_csv(resolved["verma2003_norms.csv"]).set_index("ID_Final")
    assert set(population.ID_Final) == set(data.index) and population.ID_Final.is_unique
    report = {
        "sdk_version": geonormml.__version__,
        "sdk_file": geonormml.__file__,
        "target_python": platform.python_version(),
        "original_python_recorded": False,
        "generation_id": GENERATION,
        "input_files_verified": len(hashes),
        "models": [],
        "oof": [],
        "private_report": True,
        "new_training": False,
        "external_evaluation": "not_executed",
        "unavailable_antecedent_inputs": unavailable_antecedents,
        "antecedent_scope_note": "Prior-generation weights omitted from transfer; no v4 refit/comparison is rerun.",
    }
    write_json(output / "audit-start.json", report)
    for domain in ("VOL", "PLU"):
        report["models"].append(audit_domain(domain, generation, output, population, data, norms, plan, summary))
        report["oof"].append(review_oof(generation, output, data, population, domain))
        print(f"PASS {domain} frozen model, features, SDK labels/probabilities and internal class review", flush=True)
    changed = [str(path) for path, expected in hashes.items() if digest(path) != expected]
    assert not changed, changed
    report["originals_unchanged"] = True
    report["status"] = "passed"
    write_json(output / "verification_PRIVATE.json", report)
    print(output / "verification_PRIVATE.json")


if __name__ == "__main__":
    main()
