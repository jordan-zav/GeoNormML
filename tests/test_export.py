import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier

from geonormml.features import FEATURE_SETS
from scripts import export_official_models as export


def test_transfer_schema_is_generated_from_the_exported_models(tmp_path, monkeypatch):
    df = pd.DataFrame(
        np.ones((8, len(FEATURE_SETS["combined_core"].columns))), columns=FEATURE_SETS["combined_core"].columns
    )
    df["ROCK TYPE"] = ["VOL"] * 4 + ["PLU"] * 4
    df["ROCK_NAME"] = ["a", "a", "b", "b"] * 2
    monkeypatch.setattr(export, "ARTIFACTS_DIR", tmp_path)
    monkeypatch.setattr(export, "MODELS_DIR", tmp_path / "official_models")
    monkeypatch.setattr(export, "load_training_dataset", lambda: df)
    monkeypatch.setattr(export, "get_dataset_path", lambda: Path("clean.xlsx"))
    monkeypatch.setattr(export, "training_provenance", lambda: {"dataset_sha256": "test"})
    monkeypatch.setattr(
        export, "build_models", lambda **_kwargs: {"XGBoost": DummyClassifier(), "RandomForest": DummyClassifier()}
    )
    export.main()
    root = tmp_path / "petropyqapf_transfer"
    schema = json.loads((root / "schemas/official_model_bundle.json").read_text())
    assert len(schema["official_models"]) == 2
    for spec in schema["official_models"]:
        assert not Path(spec["artifact_path"]).is_absolute()
        model = joblib.load(root / spec["artifact_path"])
        assert model["feature_columns"] == spec["required_columns"]
        assert model["classes"] == spec["classes"]
        assert model["domain_code"] == spec["domain_code"]
