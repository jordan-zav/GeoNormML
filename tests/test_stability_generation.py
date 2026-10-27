import joblib
import numpy as np
import pandas as pd
import pytest

from geonormml.stability import (
    ALGORITHMS,
    fit_model,
    geography_groups,
    predict_encoded,
    seeded_folds,
    specifications,
)
from scripts import train_stability_generation as runner


def sample_frame():
    count = 80
    frame = pd.DataFrame({"ID_Final": np.arange(count), "Sample_Group": [f"g{i // 2}" for i in range(count)],
                          "ROCK TYPE": "VOL", "ROCK_NAME": ["a"] * 40 + ["b"] * 40})
    for column in specifications()[0]["columns"]:
        frame[column] = np.arange(count, dtype=float) + 1
    return frame


def test_partition_seed_is_reproducible_and_preserves_replicates():
    frame = sample_frame()
    left = seeded_folds(frame, 5, 42)
    right = seeded_folds(frame, 5, 42)
    changed = seeded_folds(frame, 5, 137)
    for (train, valid), (again_train, again_valid) in zip(left, right):
        np.testing.assert_array_equal(train, again_train)
        np.testing.assert_array_equal(valid, again_valid)
        assert not set(frame.iloc[train].Sample_Group) & set(frame.iloc[valid].Sample_Group)
    assert set(left[0][1]) != set(changed[0][1])
    assert len(seeded_folds(frame, 3, 42)) == 3


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_new_models_fit_missing_inputs_and_roundtrip(algorithm, tmp_path):
    if algorithm == "CatBoost":
        pytest.importorskip("catboost")
    spec = next(s for s in specifications() if s["algorithm"] == algorithm and s["profile"] == "verma2003")
    frame = sample_frame()
    for column in spec["columns"]:
        if column not in frame:
            frame[column] = 0.0
    frame["Serie_Mag"] = pd.Series(["Alcalina", None] * 40, dtype=object)
    frame["Clase_SiO2"] = pd.Series(["Basica", "Intermedia"] * 40, dtype=object)
    frame.loc[::3, "LOI"] = np.nan
    model = fit_model(spec, frame, np.array([0] * 40 + [1] * 40), 2)
    prediction = predict_encoded(model, frame[spec["columns"]])
    assert prediction.shape == (80,) and set(prediction) <= {0, 1}
    path = tmp_path / "research_model.joblib"
    joblib.dump(model, path)
    np.testing.assert_array_equal(prediction, predict_encoded(joblib.load(path), frame[spec["columns"]]))
    assert runner.canonical_parameters(model) == runner.canonical_parameters(joblib.load(path))


def test_inner_search_cannot_fit_outer_or_historical_rows(monkeypatch, tmp_path):
    frame = sample_frame()
    development = frame.loc[list(range(30)) + list(range(40, 70))]
    seen = []

    class Zero:
        def predict(self, X):
            return np.zeros(len(X), dtype=int)

    def spy(spec, training, target, count):
        seen.append(set(training.index))
        return Zero()

    monkeypatch.setattr(runner, "fit_model", spy)
    specs = specifications()[:2]
    result = runner.inner_search({None: frame}, development, np.array([0] * 30 + [1] * 30),
                                 2, specs, 3, 1042, tmp_path / "search")
    assert len(result) == 2 and len(seen) == 6
    assert all(ids < set(development.index) for ids in seen)
    assert all(not ids & (set(frame.index) - set(development.index)) for ids in seen)


def test_geographic_blocks_join_cells_crossed_by_replicates():
    frame = pd.DataFrame({"LON": [-80.1, -77.9, -77.8, -70.0, np.nan],
                          "LAT": [-10.0, -10.0, -10.0, -15.0, -12.0],
                          "Sample_Group": ["replicate", "replicate", "other", "far", "missing"]})
    groups = geography_groups(frame)
    assert groups[0] == groups[1] == groups[2]
    assert groups[0] != groups[3]
    assert 4 not in groups.index
