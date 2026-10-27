"""Opt-in, read-only integration checks against the local curated baseline.

Run with GEONORMML_TEST_LOCAL_DATA=1. No data or serialized models are bundled.
"""

import hashlib
import json
import os
from collections import Counter
from pathlib import Path

import pandas as pd
import pytest
from sklearn.metrics import accuracy_score, f1_score

from geonormml.quality import clean_dataset, sample_groups

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "Dataset/Filtered/final"
ARTIFACTS = ROOT / "artifacts"
pytestmark = pytest.mark.skipif(
    os.getenv("GEONORMML_TEST_LOCAL_DATA") != "1", reason="Local dataset audit is explicitly opt-in"
)


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def baseline():
    return pd.read_excel(FINAL / "GeoNormML_training_curated.xlsx", sheet_name="training_ready_final")


def test_workbook_and_csv_match_audit_hashes():
    manifest = load_json(FINAL / "GeoNormML_training_curated.audit.json")
    for suffix, key in (("xlsx", "output_sha256"), ("csv", "csv_sha256")):
        path = FINAL / f"GeoNormML_training_curated.{suffix}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest[key]
    validation = load_json(ARTIFACTS / "validation/baseline_validation.json")
    assert validation["provenance"]["dataset_sha256"] == manifest["output_sha256"]


def test_original_population_and_classes_are_preserved(baseline):
    assert len(baseline) == baseline.ID_Final.nunique() == 2755
    assert baseline.ID_Final.notna().all()
    assert baseline["ROCK TYPE"].value_counts().to_dict() == {"VOL": 1764, "PLU": 991}
    assert baseline.groupby("ROCK TYPE").ROCK_NAME.nunique().to_dict() == {"PLU": 10, "VOL": 9}
    assert not baseline.columns.duplicated().any()


def test_every_original_measurement_matches_v4_reference(baseline):
    manifest = load_json(FINAL / "GeoNormML_training_curated.audit.json")
    reference_info = manifest["curated_reference"]
    reference_path = FINAL / reference_info["file"]
    assert hashlib.sha256(reference_path.read_bytes()).hexdigest() == reference_info["sha256"]
    reference = pd.read_excel(reference_path, sheet_name="training_ready_final").set_index("ID_Final")
    actual = baseline.set_index("ID_Final")
    pd.testing.assert_frame_equal(
        actual[reference.columns].sort_index(),
        reference.sort_index(),
        check_dtype=False,
        check_exact=False,
        rtol=1e-12,
        atol=1e-12,
    )


def test_current_cleaner_retains_every_sample_and_review_warning(baseline):
    before = baseline.copy(deep=True)
    kept, excluded, report = clean_dataset(baseline)
    pd.testing.assert_frame_equal(baseline, before)
    assert set(kept.ID_Final) == set(baseline.ID_Final)
    assert excluded.empty and report["clean_rows"] == 2755
    manifest = load_json(FINAL / "GeoNormML_training_curated.audit.json")
    assert report["review_rows_retained"] == manifest["review_rows_retained"]
    assert report["review_reasons"] == manifest["review_reasons"]


def test_holdout_preserves_population_without_sample_group_leakage(baseline):
    split = load_json(ARTIFACTS / "splits/holdout_split.json")
    train, test = set(split["train_ids"]), set(split["test_ids"])
    assert len(train) == len(split["train_ids"])
    assert len(test) == len(split["test_ids"]) == 553
    assert not train & test and train | test == set(baseline.ID_Final)
    groups = pd.Series(sample_groups(baseline).to_numpy(), index=baseline.ID_Final)
    assert not set(groups.loc[list(train)]) & set(groups.loc[list(test)])


def test_all_cv_folds_remain_inside_training_without_group_leakage(baseline):
    split = load_json(ARTIFACTS / "splits/holdout_split.json")
    folds = load_json(ARTIFACTS / "splits/cv_folds.json")["domains"]
    groups = pd.Series(sample_groups(baseline).to_numpy(), index=baseline.ID_Final)
    for domain, entries in folds.items():
        expected = set(baseline.loc[baseline["ROCK TYPE"] == domain, "ID_Final"]) & set(split["train_ids"])
        assert len(entries) == 5
        seen = Counter()
        for fold in entries:
            train, valid = set(fold["train_ids"]), set(fold["valid_ids"])
            assert len(train) == len(fold["train_ids"])
            assert len(valid) == len(fold["valid_ids"])
            assert not train & valid and train | valid == expected
            assert not set(groups.loc[list(train)]) & set(groups.loc[list(valid)])
            seen.update(valid)
        assert set(seen) == expected and set(seen.values()) == {1}


def test_saved_holdout_labels_and_metrics_match_real_samples(baseline):
    predictions = pd.read_csv(ARTIFACTS / "validation/holdout_predictions.csv")
    split = load_json(ARTIFACTS / "splits/holdout_split.json")
    assert predictions.ID_Final.is_unique
    assert set(predictions.ID_Final) == set(split["test_ids"])
    lookup = baseline.set_index("ID_Final")
    assert predictions.actual.eq(predictions.ID_Final.map(lookup.ROCK_NAME)).all()
    assert predictions.domain.eq(predictions.ID_Final.map(lookup["ROCK TYPE"])).all()
    validation = load_json(ARTIFACTS / "validation/baseline_validation.json")
    for model in validation["models"]:
        selected = predictions.loc[predictions.domain == model["domain"]]
        labels = sorted(baseline.loc[baseline["ROCK TYPE"] == model["domain"], "ROCK_NAME"].unique())
        assert len(selected) == model["holdout_rows"]
        assert accuracy_score(selected.actual, selected.predicted) == pytest.approx(model["holdout_accuracy"])
        assert f1_score(
            selected.actual, selected.predicted, labels=labels, average="macro", zero_division=0
        ) == pytest.approx(model["holdout_f1_macro"])


@pytest.mark.parametrize("profile", ["extended_cipw_v3", "verma2003", "pruseth2009"])
def test_profile_audit_accounts_for_every_sample_and_status(baseline, profile):
    audit_dir = os.getenv("GEONORMML_PROFILE_AUDIT_DIR")
    if not audit_dir:
        pytest.skip("Set GEONORMML_PROFILE_AUDIT_DIR to inspect an existing profile experiment")
    directory = Path(audit_dir)
    summary = load_json(directory / "summary.json")
    rows = pd.read_csv(directory / f"{profile}_norms.csv")
    assert rows.ID_Final.is_unique and set(rows.ID_Final) == set(baseline.ID_Final)
    observed = rows.status.value_counts().to_dict()
    assert observed == summary["norms"][profile]["status_counts"]
    assert rows.status.isin(["complete", "incomplete", "unsupported", "error", "missing_major"]).all()
    assert rows.complete.eq(rows.status.eq("complete")).all()
    assert sum(observed.values()) == len(baseline)
    assert summary["originals_unchanged"]
    for name, expected in summary["source_hashes_before"].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected


def test_publication_snapshot_reproduces_the_checked_in_evidence(baseline):
    from scripts.reconcile_publication import publication_snapshot

    expected = load_json(ROOT / "poster_cpg23/configs/current_baseline.evidence.json")
    assert publication_snapshot(FINAL / "GeoNormML_training_curated.xlsx", ARTIFACTS) == expected


def test_protocol_audit_metrics_recompute_from_every_saved_oof_prediction(baseline):
    audit_dir = os.getenv("GEONORMML_PROTOCOL_AUDIT_DIR")
    if not audit_dir:
        pytest.skip("Set GEONORMML_PROTOCOL_AUDIT_DIR to verify the controlled protocol experiment")
    directory = Path(audit_dir)
    summary = load_json(directory / "summary.json")
    predictions = pd.read_csv(directory / "oof_predictions.csv")
    source = baseline.set_index("ID_Final")
    assert predictions.actual.eq(predictions.ID_Final.map(source.ROCK_NAME)).all()
    assert len(summary["results"]) == 12
    split = load_json(ARTIFACTS / "splits/holdout_split.json")
    for record in summary["results"]:
        selected = predictions.loc[
            predictions.domain.eq(record["domain"])
            & predictions.feature_set.eq(record["feature_set"])
            & predictions.population.eq(record["population"])
            & predictions.grouped.eq(record["grouped"])
        ]
        expected = set(baseline.loc[baseline["ROCK TYPE"].eq(record["domain"]), "ID_Final"])
        if record["population"] == "recorded_training":
            expected &= set(split["train_ids"])
        assert selected.ID_Final.is_unique and set(selected.ID_Final) == expected
        assert len(selected) == record["rows"]
        assert accuracy_score(selected.actual, selected.predicted) == pytest.approx(record["accuracy"], abs=1e-12)
    assert not summary["cipw_recalculated"] and not summary["models_exported"]
