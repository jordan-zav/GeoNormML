"""Prevent local research files from leaking into a public Python release."""

import pytest

from scripts.check_distribution import check_names


@pytest.mark.parametrize("name", [
    "geonormml-0.1.0/Dataset/private.xlsx",
    "geonormml-0.1.0/artifacts/private.joblib",
    "geonormml/weights.pkl",
    "geonormml/.env.production",
    "geonormml/.devresources.local.cmd",
    "geonormml/AGENTS.md",
    "geonormml/auth.json",
    "../outside.py",
])
def test_public_distribution_rejects_private_inputs_and_configuration(name):
    with pytest.raises(ValueError):
        check_names([name])


def test_public_code_and_historical_metadata_are_allowed():
    check_names([
        "geonormml/catalog.py",
        "geonormml-0.1.0/poster_cpg23/configs/current_baseline.evidence.json",
        "geonormml-0.1.0/docs/PUBLISHING.md",
    ])
