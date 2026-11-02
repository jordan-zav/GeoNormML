"""Public synthetic tests for model contracts and row-preserving application inference."""

import json
import platform

import joblib
import numpy as np
import pandas as pd
import pytest

from geonormml import ModelError, inspect_model, list_models, load_model, predict
from geonormml.cli import main
from geonormml.examples import create_example
from geonormml.models import create_model_manifest


@pytest.fixture
def example(tmp_path):
    return create_example(tmp_path / "synthetic")


def edit_manifest(example, **changes):
    path = example["manifest"]
    with open(path, encoding="utf-8") as stream:
        metadata = json.load(stream)
    metadata.update(changes)
    with open(path, "w", encoding="utf-8") as stream:
        json.dump(metadata, stream)
    return metadata


def test_inspection_never_deserializes_and_load_requires_trust(example, monkeypatch):
    monkeypatch.setattr(joblib, "load", lambda *_a, **_k: pytest.fail("Unexpected deserialization"))
    info = inspect_model(example["manifest"])
    assert info["verified"] and info["normative"]["profile"] == "verma2003"
    assert len(list_models(example["directory"])) == 1
    with pytest.raises(ModelError, match="trusted=True"):
        load_model(example["manifest"])
    edit_manifest(example, model_sha256="0" * 64)
    with pytest.raises(ModelError) as error:
        load_model(example["manifest"], trusted=True)
    assert error.value.code == "checksum_mismatch"


@pytest.mark.parametrize(
    "changes,code",
    [
        ({"model_file": "../outside.joblib"}, "invalid_manifest"),
        ({"model_file": "C:/outside.joblib"}, "invalid_manifest"),
        ({"classes": ["same", "same"]}, "invalid_manifest"),
        ({"normative": None}, "invalid_manifest"),
        ({"python_version": "1.0"}, "environment_mismatch"),
        ({"dependencies": {"numpy": "0"}}, "invalid_manifest"),
    ],
)
def test_bad_contracts_fail_before_loading(example, changes, code, monkeypatch):
    edit_manifest(example, **changes)
    monkeypatch.setattr(joblib, "load", lambda *_a, **_k: pytest.fail("Invalid model was loaded"))
    with pytest.raises(ModelError) as error:
        load_model(example["manifest"], trusted=True)
    assert error.value.code == code


def test_environment_mismatch_fails_without_loading(example, monkeypatch):
    metadata = edit_manifest(example)
    metadata["dependencies"]["scikit-learn"] = "0"
    edit_manifest(example, **metadata)
    monkeypatch.setattr(joblib, "load", lambda *_a, **_k: pytest.fail("Invalid environment was loaded"))
    with pytest.raises(ModelError) as error:
        load_model(example["manifest"], trusted=True)
    assert error.value.code == "environment_mismatch"


def test_predictions_retain_every_row_id_and_index_and_ignore_stale_norms(example):
    frame = pd.read_csv(example["input"], dtype={"Sample_ID": str})
    frame.index = [99, 7, 7, 2]
    frame["Q"] = -9999
    frame["Clase_SiO2"] = "stale"
    frame["ROCK TYPE"] = ["VOL", "PLU", "VOL", "VOL"]
    frame.iloc[2, frame.columns.get_loc("SiO2")] = np.nan
    frame.iloc[3, frame.columns.get_loc("Na2O")] = -1
    original = frame.copy(deep=True)
    model = load_model(example["manifest"], trusted=True)
    result = model.predict(frame, id_column="Sample_ID")
    pd.testing.assert_frame_equal(frame, original)
    assert result.index.tolist() == [99, 7, 7, 2]
    assert result.sample_id.tolist() == ["001", "002", "003", "004"]
    assert result.status.tolist() == ["predicted", "rejected", "rejected", "rejected"]
    assert result.error_code.tolist() == ["", "domain_mismatch", "missing_major", "negative_oxide"]
    assert result.prediction.iloc[1:].isna().all()
    assert result.filter(like="probability::").iloc[1:].isna().all().all()
    assert result.filter(like="probability::").iloc[0].sum() == pytest.approx(1)
    model.manifest["classes"][0] = "changed_copy"
    assert model.manifest["classes"][0] == "Synthetic_A"


def test_numeric_failure_does_not_suppress_valid_rows_and_negative_loi_is_allowed(example):
    frame = pd.read_csv(example["input"])
    frame["FeOT"] = frame["FeOT"].astype(object)
    frame.loc[0, "FeOT"] = "bad"
    frame.loc[2, "FeOT"] = np.inf
    frame.loc[3, "FeOT"] = True
    result = predict(frame, example["manifest"], trusted=True)
    assert result.status.tolist() == ["rejected", "predicted", "rejected", "rejected"]
    assert result.error_code.iloc[[0, 2, 3]].eq("invalid_numeric_input").all()


def test_missing_headers_and_empty_input_are_explicit(example):
    frame = pd.read_csv(example["input"])
    model = load_model(example["manifest"], trusted=True)
    with pytest.raises(ModelError) as error:
        model.predict(frame.drop(columns="SiO2"))
    assert error.value.code == "missing_columns"
    result = model.predict(frame.iloc[:0])
    assert result.empty and "status" in result


def test_prepared_feature_mode_uses_existing_features_without_engine_recomputation(example):
    from geonormml.inference import _prepare_frame

    model = load_model(example["manifest"], trusted=True)
    frame = pd.read_csv(example["input"])
    features, _ = _prepare_frame(frame, model.manifest)
    metadata = edit_manifest(
        example, input_mode="prepared_features", normative=None, categorical_columns=["Clase_SiO2", "Serie_Mag"]
    )
    prepared = load_model(example["manifest"], trusted=True)
    np.testing.assert_allclose(
        prepared.predict(features).filter(like="probability::"),
        model.predict(frame).filter(like="probability::"),
    )
    assert metadata["python_version"] == ".".join(platform.python_version_tuple()[:2])


def test_manifest_contract_mismatch_is_not_silently_accepted(example):
    edit_manifest(example, generation_id="wrong-generation")
    with pytest.raises(ModelError) as error:
        load_model(example["manifest"], trusted=True)
    assert error.value.code == "bundle_mismatch"


def test_a_different_normative_contract_cannot_be_substituted_in_the_manifest(example):
    metadata = edit_manifest(example)
    metadata["normative"]["fe3_fraction"] = 0.3
    edit_manifest(example, **metadata)
    with pytest.raises(ModelError) as error:
        load_model(example["manifest"], trusted=True)
    assert error.value.code == "bundle_mismatch"


def test_malformed_serialized_class_metadata_has_a_structured_error(example, tmp_path):
    from pathlib import Path

    payload = joblib.load(Path(example["directory"]) / "model.joblib")
    payload.pop("classes")
    payload["label_encoder"] = None
    artifact = tmp_path / "malformed.joblib"
    joblib.dump(payload, artifact)
    metadata = json.loads(Path(example["manifest"]).read_text(encoding="utf-8"))
    manifest = create_model_manifest(artifact, metadata)
    with pytest.raises(ModelError) as error:
        load_model(manifest, trusted=True)
    assert error.value.code == "bundle_mismatch"


def test_label_encoded_models_without_probabilities_do_not_fabricate_scores(example, tmp_path):
    from pathlib import Path

    from sklearn.pipeline import Pipeline
    from sklearn.svm import SVC

    from geonormml.inference import _prepare_frame
    from geonormml.ml import build_preprocessor

    metadata = json.loads(Path(example["manifest"]).read_text(encoding="utf-8"))
    metadata["prediction_encoding"] = "labels"
    frame = pd.read_csv(example["input"])
    features, _ = _prepare_frame(frame, metadata)
    estimator = Pipeline(
        [
            ("features", build_preprocessor(metadata["feature_columns"], features)),
            ("model", SVC(probability=False)),
        ]
    ).fit(features, ["Synthetic_A", "Synthetic_B", "Synthetic_A", "Synthetic_B"])
    payload = {
        key: metadata[key]
        for key in (
            "generation_id",
            "domain_code",
            "feature_columns",
            "classes",
            "input_mode",
            "feature_set",
            "normative",
        )
    }
    payload["estimator"] = estimator
    artifact = tmp_path / "labels-only.joblib"
    joblib.dump(payload, artifact)
    manifest = create_model_manifest(artifact, metadata)
    result = predict(frame, manifest, trusted=True)
    assert result.prediction.isin(metadata["classes"]).all()
    assert result.filter(like="probability::").isna().all().all()


def test_cli_writes_new_csv_without_changing_inputs_and_returns_json(example, tmp_path, capsys):
    from pathlib import Path

    source = Path(example["input"])
    original = source.read_bytes()
    destination = tmp_path / "predictions.csv"
    args = [
        "predict",
        "--model",
        example["manifest"],
        "--input",
        str(source),
        "--output",
        str(destination),
        "--id-column",
        "Sample_ID",
        "--trust-model",
    ]
    assert main(args) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["ok"] and report["predicted"] == 4
    assert pd.read_csv(destination, dtype={"sample_id": str}).sample_id.tolist() == ["001", "002", "003", "004"]
    assert source.read_bytes() == original
    existing = destination.read_bytes()
    assert main(args) == 2
    assert destination.read_bytes() == existing
    assert not json.loads(capsys.readouterr().err)["ok"]


def test_model_and_manifest_outputs_never_overwrite_existing_files(example):
    from pathlib import Path

    manifest = Path(example["manifest"])
    old = manifest.read_bytes()
    with pytest.raises(FileExistsError):
        create_model_manifest(Path(example["directory"]) / "model.joblib", json.loads(old))
    assert manifest.read_bytes() == old
    with pytest.raises(FileExistsError):
        create_example(example["directory"])
