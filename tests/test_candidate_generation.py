import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin

from geonormml import generation
from geonormml.features import CIPW_FEATURES, OXIDE_FEATURES_CORE


class RecordingClassifier(ClassifierMixin, BaseEstimator):
    fit_inputs = []

    def fit(self, X, y):
        type(self).fit_inputs.append(set(X.SiO2))
        self.classes_ = np.unique(y)
        return self

    def predict(self, X):
        return np.zeros(len(X), dtype=int)


def test_inner_selection_cannot_fit_outer_validation_or_holdout_rows(monkeypatch):
    count = 80
    frame = pd.DataFrame({column: np.arange(count, dtype=float) + 1 for column in OXIDE_FEATURES_CORE})
    frame[list(CIPW_FEATURES)] = 0.0
    frame["ID_Final"] = np.arange(count)
    frame["Source"] = "lab"
    frame["LAB_ID"] = [f"group-{i // 2}" for i in range(count)]
    frame["ROCK TYPE"] = "VOL"
    frame["ROCK_NAME"] = ["a"] * 40 + ["b"] * 40
    development = frame.loc[list(range(30)) + list(range(40, 70))]
    target = np.array([0] * 30 + [1] * 30)
    frames = {profile: frame.copy() for profile in (None, *generation.PROFILES)}
    RecordingClassifier.fit_inputs = []
    monkeypatch.setattr(generation, "template_for", lambda *_args: RecordingClassifier())
    selected, scores = generation.select_candidate(frames, development, target, 2, 3)
    assert len(scores) == 8 and len(RecordingClassifier.fit_inputs) == 24
    assert all(fit <= set(development.SiO2) for fit in RecordingClassifier.fit_inputs)
    assert all(
        not fit & set(frame.loc[~frame.index.isin(development.index)].SiO2) for fit in RecordingClassifier.fit_inputs
    )
    assert selected["profile"] is None and selected["model_name"] == "RandomForest"


def test_candidate_contract_has_no_spatial_or_label_features():
    for spec in generation.candidate_specs():
        columns = generation.columns_for(spec)
        assert not set(columns) & {"LAT", "LON", "ROCK_NAME", "Quality_Flag", "Sample_Group", "Trench_Dist"}
        assert len(columns) == (39 if spec["profile"] else 12)
    assert generation.PLAN["outer_folds"] == 5 and generation.PLAN["inner_folds"] == 3
    assert generation.PLAN["selection_order"][0] == "f1_macro"
