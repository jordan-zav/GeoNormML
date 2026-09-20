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


def test_quarantine_keeps_row_accounting_and_missing_loi(samples):
    samples.loc[0, "mass_balance_error"] = 0.2
    samples.loc[1, "SiO2"] = np.nan
    samples.loc[2, "FeOT"] = -1.0
    samples.loc[3, "LOI"] = -0.2
    clean, excluded, report = clean_dataset(samples)
    assert len(clean) == 5 and len(excluded) == 3
    assert clean.ID_Final.is_unique
    assert clean.loc[clean.ID_Final.eq(4), "LOI"].iloc[0] == -0.2
    assert clean.LOI.isna().sum() == 4
    assert report["input_rows"] == report["clean_rows"] + len(excluded)


def test_exact_chemistry_conflicting_labels_is_not_reclassified(samples):
    samples.loc[1, CORE] = samples.loc[0, CORE]
    samples.loc[1, "ROCK_NAME"] = "basalto"
    clean, excluded, _ = clean_dataset(samples)
    assert len(clean) == 6
    assert set(excluded.QC_Reason) == {"identical_chemistry_conflicting_labels"}
    assert set(excluded.ROCK_NAME) == {"andesita", "basalto"}


def test_duplicate_assays_keep_lowest_original_id(samples):
    repeated = samples.iloc[[0]].copy()
    repeated.ID_Final = 20
    clean, excluded, _ = clean_dataset(pd.concat([repeated, samples], ignore_index=True))
    assert 1 in clean.ID_Final.values and 20 not in clean.ID_Final.values
    assert excluded.QC_Reason.tolist() == ["duplicate_analysis"]


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
