"""Public synthetic integration checks; no research dataset or model is loaded."""

import io
from importlib.metadata import version

import geonormpy
import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier
from sklearn.pipeline import Pipeline

from geonormml.expanded import profile_frame
from geonormml.features import FEATURE_SETS
from geonormml.generation import PLAN, PROFILES
from geonormml.ml import build_preprocessor


def test_engine_runtime_and_installed_metadata_match_frozen_contract():
    expected = PLAN["cipw"]["required_engine_version"]
    assert geonormpy.__version__ == version("geonormpy") == expected == "1.1.0"
    assert set(geonormpy.available_profiles()["profiles"]) == set(PROFILES)


@pytest.mark.parametrize("profile", PROFILES)
def test_real_norms_feed_features_preprocessing_and_serialized_prediction(profile):
    # These are invented chemical inputs and arbitrary labels, not rock benchmarks.
    chemistry = pd.DataFrame(
        {
            "SiO2": [70.0, 55.0, 68.0, 53.0],
            "TiO2": [0.5, 1.0, 0.6, 1.1],
            "Al2O3": [15.0, 17.0, 15.5, 17.5],
            "FeOT": [3.0, 7.0, 3.5, 7.5],
            "MgO": [1.0, 4.0, 1.5, 4.5],
            "CaO": [2.0, 7.0, 2.5, 7.5],
            "Na2O": [4.0, 4.0, 4.0, 4.0],
            "K2O": [4.0, 2.0, 3.5, 1.5],
            "P2O5": [0.2, 0.3, 0.2, 0.3],
            "MnO": [0.1, 0.2, 0.1, 0.2],
            "F": [0.1, 0.1, 0.1, 0.1],
            "LOI": [np.nan, -0.1, 0.2, 0.3],
            "Sum_Oxs": [np.nan, 99.5, 99.7, 100.0],
        },
        index=pd.Index([41, 7, 98, 13], name="sample"),
    )
    original = chemistry.copy(deep=True)
    records = []
    for _, row in chemistry.iterrows():
        inputs = {key: float(row[key]) for key in PLAN["cipw"]["input_keys"] if key in row and pd.notna(row[key])}
        norm = geonormpy.cipw(
            inputs,
            profile=profile,
            iron_policy="fixed",
            fe3_fraction=0.15,
            carbonate_mode="calcite",
            strict=False,
            mass_tol=1e-6,
        )
        assert norm["flags"]["calculation_complete"]
        assert norm["calculation_metadata"]["profile"] == profile
        records.append({"phase_" + phase: value for phase, value in norm["minerals_wtpercent"].items()})
    norms = pd.DataFrame(records, index=chemistry.index)
    features = profile_frame(chemistry, norms)
    pd.testing.assert_frame_equal(chemistry, original)
    assert features.index.equals(chemistry.index)
    assert features.Ap.to_numpy() == pytest.approx(norms.get("phase_Ap", 0) + norms.get("phase_FAp", 0))
    assert features.loc[7, "LOI"] == -0.1
    columns = list(FEATURE_SETS["combined_enriched"].columns)
    matrix = features[columns]
    pipeline = Pipeline(
        [
            ("features", build_preprocessor(columns, matrix)),
            ("model", DummyClassifier(strategy="prior")),
        ]
    )
    # A tiny plumbing fixture only; never trains or evaluates a research classifier.
    pipeline.fit(matrix, [0, 1, 0, 1])
    assert np.isfinite(pipeline.named_steps["features"].transform(matrix)).all()
    expected = pipeline.predict_proba(matrix)
    buffer = io.BytesIO()
    joblib.dump(pipeline, buffer)
    buffer.seek(0)
    np.testing.assert_allclose(joblib.load(buffer).predict_proba(matrix), expected)


def test_failed_norm_is_explicit_and_not_a_zero_mineral_vector():
    result = geonormpy.cipw_safe({"SiO2": -1}, profile="verma2003")
    assert not result["ok"]
    assert result["result"] is None
    assert result["error"]["code"]
