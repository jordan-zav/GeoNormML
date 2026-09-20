import io

import joblib
import numpy as np
import pandas as pd
import pytest

from geonormml import config
from geonormml.data import _compute_trench_distance, derive_features, validate_training_frame
from geonormml.ml import build_models, build_preprocessor
from geonormml.quality import sample_groups
from geonormml.split import grouped_cv_indices, make_cv_folds, make_holdout_split


def test_logging_accepts_notebook_stdout(monkeypatch):
    stream = io.StringIO()
    monkeypatch.setattr(config.sys, "stdout", stream)
    logger = config.setup_logging("test.notebook")
    logger.info("hello")
    assert "hello" in stream.getvalue()
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)


def test_logging_handles_unicode_in_redirected_windows_output(monkeypatch):
    buffer = io.BytesIO()
    stream = io.TextIOWrapper(buffer, encoding="cp1252")
    monkeypatch.setattr(config.sys, "stdout", stream)
    logger = config.setup_logging("test.windows.output")
    logger.info("etapa → salida")
    stream.flush()
    assert "etapa → salida" in buffer.getvalue().decode("utf-8")
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)


def test_dataset_resolution_is_dynamic(monkeypatch, tmp_path):
    clean = tmp_path / "clean.xlsx"
    spatial = tmp_path / "spatial.xlsx"
    consistent = tmp_path / "consistent.xlsx"
    monkeypatch.delenv("GEONORMML_DATASET_PATH", raising=False)
    monkeypatch.setattr(config, "CLEAN_DATASET", clean)
    monkeypatch.setattr(config, "SPATIAL_DATASET", spatial)
    monkeypatch.setattr(config, "CONSISTENT_DATASET", consistent)
    consistent.touch()
    assert config.get_dataset_path() == consistent
    spatial.touch()
    assert config.get_dataset_path() == spatial
    clean.touch()
    assert config.get_dataset_path() == clean
    monkeypatch.setenv("GEONORMML_DATASET_PATH", str(consistent))
    assert config.get_dataset_path() == consistent


def test_missing_measurements_do_not_become_zero_indices():
    df = pd.DataFrame(
        {
            "Al2O3": [15.0, 15.0],
            "CaO": [np.nan, 0.0],
            "Na2O": [3.0, 0.0],
            "K2O": [2.0, 0.0],
            "MgO": [4.0, 0.0],
            "FeOT": [np.nan, 0.0],
            "An": [0.0, np.nan],
            "Ab": [0.0, 1.0],
        }
    )
    result = derive_features(df)
    assert result[["ASI", "Mg_num", "%An en Pl"]].isna().all().all()
    assert result.SUM_CIPW.isna().all()


def test_unknown_coordinates_are_not_zero_distance():
    result = _compute_trench_distance(np.array([np.nan, -82.0, 200.0]), np.array([-10.0, -4.0, -10.0]))
    assert np.isnan(result[0]) and np.isnan(result[2])
    assert result[1] == 0.0


@pytest.fixture
def grouped_samples():
    return pd.DataFrame(
        [
            {
                "ID_Final": i,
                "Source": "lab",
                "LAB_ID": f"sample-{i // 2}",
                "ROCK_NAME": "a" if i < 40 else "b",
                "ROCK TYPE": "VOL",
            }
            for i in range(80)
        ]
    )


def test_validation_keeps_replicates_together_and_holdout_out_of_cv(grouped_samples):
    df = grouped_samples
    groups = sample_groups(df)
    holdout = make_holdout_split(df, "ID_Final")
    train = df[df.ID_Final.isin(holdout.train_ids)]
    assert not set(groups[df.ID_Final.isin(holdout.train_ids)]) & set(groups[df.ID_Final.isin(holdout.test_ids)])
    folds = make_cv_folds(train, "ID_Final")
    assert set().union(*(set(f["valid_ids"]) for f in folds)) == set(holdout.train_ids)
    assert not set().union(*(set(f["valid_ids"]) for f in folds)) & set(holdout.test_ids)
    assert holdout == make_holdout_split(df, "ID_Final")


def test_duplicate_ids_and_insufficient_groups_fail(grouped_samples):
    df = grouped_samples
    with pytest.raises(ValueError, match="Duplicate ID_Final"):
        validate_training_frame(pd.concat([df, df.iloc[[0]]]))
    df["LAB_ID"] = "same-sample"
    with pytest.raises(ValueError, match="sample groups"):
        grouped_cv_indices(df)


@pytest.mark.parametrize("model_name", ["RandomForest", "SVM_PCA", "XGBoost"])
def test_model_handles_empty_features_and_roundtrips(model_name, tmp_path):
    df = pd.DataFrame(
        {"SiO2": [45.0, 46.0, 47.0, 60.0, 61.0, 62.0] * 3, "empty_oxide": [np.nan] * 18, "context": [np.nan] * 18}
    )
    df["context"] = df.context.astype(object)
    model = build_models(2, build_preprocessor(list(df), df))[model_name]
    model.fit(df, [0, 0, 0, 1, 1, 1] * 3)
    assert np.isfinite(model.predict_proba(df)).all()
    path = tmp_path / "model.joblib"
    joblib.dump(model, path)
    assert np.allclose(model.predict_proba(df), joblib.load(path).predict_proba(df))


def test_binary_roc_is_supported():
    from scripts.run_ml_benchmark import compute_multiclass_roc

    score, payload = compute_multiclass_roc(
        np.array([0, 1, 0, 1]), np.array([[0.8, 0.2], [0.1, 0.9], [0.9, 0.1], [0.2, 0.8]]), ["a", "b"]
    )
    assert score == 1.0 and set(payload["per_class"]) == {"a", "b"}
