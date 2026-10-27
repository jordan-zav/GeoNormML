"""The profile audit must preserve its coverage denominator and be safe to inspect."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.report_cipw_profile_comparison import coverage_counts


def test_coverage_preserves_rows_with_unsupported_inputs_and_errors():
    statuses = {"complete": 2700, "incomplete": 20, "unsupported": 19, "error": 2, "missing_major": 14}
    result = coverage_counts(statuses)
    assert result["outside_scope"] == 21
    assert sum(result.values()) == 2755


def test_coverage_supports_an_experiment_without_any_failures():
    assert coverage_counts({"complete": 10}) == {
        "complete": 10,
        "incomplete": 0,
        "outside_scope": 0,
        "missing_major": 0,
    }


@pytest.mark.parametrize("invalid", [-1, 1.5, True])
def test_coverage_rejects_invalid_counts(invalid):
    with pytest.raises(ValueError, match="nonnegative integers"):
        coverage_counts({"complete": invalid})


def test_coverage_rejects_unknown_status_instead_of_dropping_rows():
    with pytest.raises(ValueError, match="Unknown calculation status"):
        coverage_counts({"complete": 3, "unrecognized": 2})


@pytest.mark.parametrize("name", ["compare_cipw_profiles.py", "report_cipw_profile_comparison.py"])
def test_audit_help_needs_no_datasets_models_or_output_directory(tmp_path, name):
    script = Path(__file__).resolve().parents[1] / "scripts" / name
    result = subprocess.run(
        [sys.executable, "-B", str(script), "--help"],
        cwd=tmp_path,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "--output" in result.stdout
    assert not list(tmp_path.iterdir())
