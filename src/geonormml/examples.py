"""Generate an explicitly synthetic, user-owned example without private resources."""

import platform
from pathlib import Path


def create_example(directory):
    import joblib
    import numpy as np
    import pandas as pd
    from sklearn.dummy import DummyClassifier
    from sklearn.pipeline import Pipeline

    from .features import FEATURE_SETS
    from .inference import _prepare_frame
    from .ml import build_preprocessor
    from .models import create_model_manifest, runtime_dependencies

    root = Path(directory).expanduser().resolve()
    if root.exists():
        raise FileExistsError(f"Preserve the existing directory; choose a new example destination: {root}")
    frame = pd.DataFrame(
        {
            "Sample_ID": ["001", "002", "003", "004"],
            "SiO2": [70, 55, 68, 53],
            "TiO2": [0.5, 1, 0.6, 1.1],
            "Al2O3": [15, 17, 15.5, 17.5],
            "FeOT": [3, 7, 3.5, 7.5],
            "MgO": [1, 4, 1.5, 4.5],
            "CaO": [2, 7, 2.5, 7.5],
            "Na2O": [4, 4, 4, 4],
            "K2O": [4, 2, 3.5, 1.5],
            "P2O5": [0.2, 0.3, 0.2, 0.3],
            "MnO": [0.1, 0.2, 0.1, 0.2],
            "LOI": [np.nan, -0.1, 0.2, 0.3],
            "Sum_Oxs": [np.nan, 99.5, 99.7, 100],
        }
    )
    manifest = {
        "generation_id": "synthetic-plumbing-example-v1",
        "domain_code": "VOL",
        "input_mode": "oxide_chemistry",
        "feature_set": "combined_contextual",
        "feature_columns": list(FEATURE_SETS["combined_contextual"].columns),
        "classes": ["Synthetic_A", "Synthetic_B"],
        "prediction_encoding": "encoded",
        "python_version": ".".join(platform.python_version_tuple()[:2]),
        "dependencies": runtime_dependencies(),
        "normative": {
            "engine_version": "1.1.0",
            "profile": "verma2003",
            "profile_version": "1.0",
            "iron_policy": "fixed",
            "fe3_fraction": 0.15,
            "carbonate_mode": "calcite",
            "apatite_feature": "Ap + FAp",
        },
        "description": "Synthetic chemistry and arbitrary labels; DummyClassifier tests plumbing, not rock accuracy.",
    }
    features, errors = _prepare_frame(frame, manifest)
    if errors.ne("").any():
        raise ValueError("Synthetic fixture failed the declared normative contract")
    estimator = Pipeline(
        [
            ("features", build_preprocessor(manifest["feature_columns"], features)),
            ("model", DummyClassifier(strategy="prior")),
        ]
    ).fit(features, [0, 1, 0, 1])
    root.mkdir(parents=True, exist_ok=False)
    artifact = root / "model.joblib"
    joblib.dump(
        {
            "estimator": estimator,
            "classes": manifest["classes"],
            "feature_columns": manifest["feature_columns"],
            "generation_id": manifest["generation_id"],
            "domain_code": manifest["domain_code"],
            "input_mode": manifest["input_mode"],
            "feature_set": manifest["feature_set"],
            "normative": manifest["normative"],
        },
        artifact,
    )
    path = create_model_manifest(artifact, manifest)
    frame.to_csv(root / "input.csv", index=False)
    return {
        "directory": str(root),
        "manifest": str(path),
        "input": str(root / "input.csv"),
        "note": manifest["description"],
    }
