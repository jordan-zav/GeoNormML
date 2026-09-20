import json

import numpy as np
import pandas as pd
import pytest

from geonormml.quality import (
    CORE,
    clean_dataset,
    collapse_spatial_matches,
    ensure_clean_training_dataset,
    sample_groups,
    write_clean_dataset,
)


@pytest.fixture
def samples():
    rows = []
    for i in range(8):
        rows.append(
            {
                "ID_Final": i + 1,
                "Source": "lab",
                "LAB_ID": str(i),
                "ROCK TYPE": "VOL",
                "ROCK_NAME": "andesita",
                "SiO2": 55 + i,
                "Al2O3": 15.0,
                "FeOT": 8.0,
                "MgO": 4.0,
                "CaO": 6.0,
                "Na2O": 3.0,
                "K2O": 2.0,
                "mass_balance_error": 0.01,
                "LOI": np.nan,
                "Metal_Belt": "A",
            }
        )
    return pd.DataFrame(rows)


def test_spatial_duplicates_do_not_multiply_samples(samples):
    repeated = samples.iloc[[0]].copy()
    repeated["Metal_Belt"] = "B"
    clean, excluded, report = clean_dataset(pd.concat([samples, repeated], ignore_index=True))
    assert len(clean) == 8 and len(excluded) == 1
    assert pd.isna(clean.loc[0, "Metal_Belt"])
    assert json.loads(clean.loc[0, "Metal_Belt_Candidates"]) == ["A", "B"]
    assert report["spatial_duplicate_rows_removed"] == 1


def test_conflicting_duplicate_ids_fail_without_arbitrary_choice(samples):
    repeated = samples.iloc[[0]].copy()
    repeated["SiO2"] = 70.0
    with pytest.raises(ValueError, match="conflicting sample"):
        collapse_spatial_matches(pd.concat([samples, repeated]), ["Metal_Belt"])


def test_review_flags_preserve_curated_ids_and_values(samples):
    samples.loc[0, "mass_balance_error"] = 0.2
    samples.loc[1, "SiO2"] = np.nan
    samples.loc[2, "FeOT"] = -1.0
    samples.loc[3, "LOI"] = -0.2
    clean, excluded, report = clean_dataset(samples)
    assert len(clean) == 8 and excluded.empty
    assert report["review_rows_retained"] == 3
    assert report["quarantined_or_duplicate_rows"] == 0
    assert clean.loc[clean.ID_Final.eq(4), "LOI"].iloc[0] == -0.2
    assert clean.LOI.isna().sum() == 7


def test_conflicting_labels_are_retained_for_review(samples):
    samples.loc[1, CORE] = samples.loc[0, CORE]
    samples.loc[1, "ROCK_NAME"] = "basalto"
    clean, excluded, report = clean_dataset(samples)
    assert len(clean) == 8 and excluded.empty
    flagged = clean[clean.QC_Review.ne("")]
    assert set(flagged.QC_Review) == {"identical_chemistry_conflicting_labels"}
    assert set(flagged.ROCK_NAME) == {"andesita", "basalto"}
    assert report["review_rows_retained"] == 2
    assert flagged.Sample_Group.nunique() == 1


def test_duplicate_assays_with_distinct_curated_ids_are_retained(samples):
    repeated = samples.iloc[[0]].copy()
    repeated.ID_Final = 20
    clean, excluded, report = clean_dataset(pd.concat([repeated, samples], ignore_index=True))
    assert set(clean.ID_Final) == set(samples.ID_Final) | {20}
    assert excluded.empty
    assert clean.loc[clean.ID_Final.eq(20), "QC_Review"].iloc[0] == "duplicate_analysis"
    assert clean.loc[clean.ID_Final.isin([1, 20]), "Sample_Group"].nunique() == 1
    assert report["review_rows_retained"] == 1


def test_restrictive_filter_requires_explicit_experimental_policy(samples):
    samples.loc[0, "mass_balance_error"] = 0.2
    clean, excluded, report = clean_dataset(samples, policy="restricted_experiment")
    assert len(clean) == 7 and len(excluded) == 1
    assert report["policy_id"] == "restricted_experiment"


def test_replicate_groups_are_transitive(samples):
    samples.loc[1, "LAB_ID"] = samples.loc[0, "LAB_ID"]
    samples.loc[2, CORE] = samples.loc[1, CORE]
    groups = sample_groups(samples)
    assert groups.iloc[0] == groups.iloc[1] == groups.iloc[2]
    assert groups.iloc[3] != groups.iloc[0]


def test_clean_export_never_overwrites_source_or_existing_output(samples, tmp_path):
    source = tmp_path / "source.xlsx"
    samples.to_excel(source, sheet_name="training_ready_final", index=False)
    original = source.read_bytes()
    with pytest.raises(ValueError, match="overwrite"):
        write_clean_dataset(source, source)
    output = tmp_path / "clean.xlsx"
    report = write_clean_dataset(source, output)
    assert source.read_bytes() == original
    assert report["clean_rows"] == 8
    assert output.with_suffix(".audit.json").exists()
    with pytest.raises(FileExistsError):
        write_clean_dataset(source, output)


def test_pipeline_reuses_only_unmodified_audited_data(samples, tmp_path):
    source = tmp_path / "source.xlsx"
    samples.to_excel(source, sheet_name="training_ready_final", index=False)
    output = ensure_clean_training_dataset(source, tmp_path)
    assert output != source
    assert ensure_clean_training_dataset(output, tmp_path) == output
    assert ensure_clean_training_dataset(source, tmp_path) == output
    output.write_bytes(output.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="changed since its audit"):
        ensure_clean_training_dataset(output, tmp_path)


def test_pipeline_rejects_old_restrictive_dataset(samples, tmp_path):
    source = tmp_path / "source.xlsx"
    samples.to_excel(source, sheet_name="training_ready_final", index=False)
    restricted = tmp_path / "restricted.xlsx"
    write_clean_dataset(source, restricted, policy="restricted_experiment")
    with pytest.raises(ValueError, match="not the curated baseline"):
        ensure_clean_training_dataset(restricted, tmp_path)
    from geonormml.data import load_training_dataset

    with pytest.raises(ValueError, match="not the curated baseline"):
        load_training_dataset(restricted)


def test_reference_validation_blocks_unapproved_sample_reduction(samples, tmp_path):
    source = tmp_path / "source.xlsx"
    reference = tmp_path / "reference.xlsx"
    samples.to_excel(reference, sheet_name="training_ready_final", index=False)
    samples.iloc[1:].to_excel(source, sheet_name="training_ready_final", index=False)
    output = tmp_path / "curated.xlsx"
    with pytest.raises(ValueError, match="reference IDs"):
        write_clean_dataset(source, output, reference=reference)
    assert not output.exists()


def test_reference_validation_records_full_preservation(samples, tmp_path):
    source = tmp_path / "source.xlsx"
    samples.to_excel(source, sheet_name="training_ready_final", index=False)
    output = tmp_path / "curated.xlsx"
    report = write_clean_dataset(source, output, reference=source)
    assert report["curated_reference"]["all_ids_and_original_values_preserved"]
    assert report["curated_reference"]["rows"] == len(samples)
