"""Recorded diagnostics must distinguish unsupported chemistry from solver errors."""

import pytest

from scripts.compare_cipw_profiles import calculation_error_status


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("unsupported_profile_oxide", "unsupported"),
        ("unsupported_component", "unsupported"),
        ("unsupported_oxide", "error"),
        ("allocation_invariant", "error"),
        ("invalid_measurement", "error"),
        (None, "error"),
    ],
)
def test_error_status_preserves_applicability_and_real_failures(code, expected):
    error = ValueError("diagnostic")
    if code is not None:
        error.code = code
    assert calculation_error_status(error) == expected
