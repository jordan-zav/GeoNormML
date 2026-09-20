import sys

import pytest

from scripts import apply_quality_filter, assign_final_ids, finalize_consistent_training_dataset, run_pipeline


@pytest.mark.parametrize("module", [apply_quality_filter, assign_final_ids, finalize_consistent_training_dataset])
def test_missing_input_does_not_report_success(module, tmp_path, monkeypatch):
    monkeypatch.setattr(module, "INPUT_PATH", tmp_path / "missing.xlsx")
    monkeypatch.setattr(module, "OUTPUT_DIR", tmp_path)
    with pytest.raises(FileNotFoundError):
        module.main()


def test_invalid_pipeline_range_fails(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["run_pipeline", "--from-step", "99", "--dry-run"])
    with pytest.raises(SystemExit) as error:
        run_pipeline.main()
    assert error.value.code == 2


def test_spatial_skip_does_not_reuse_stale_spatial_dataset(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["run_pipeline", "--skip-spatial", "--dry-run"])
    monkeypatch.setenv("GEONORMML_DATASET_PATH", "stale-spatial.xlsx")
    run_pipeline.main()
    from geonormml.config import get_dataset_path

    assert get_dataset_path() == run_pipeline.CONSISTENT_DATASET
