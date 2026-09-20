"""Capture training input and dependency versions alongside exported models."""

import hashlib
from importlib.metadata import version

from .config import get_dataset_path


def training_provenance():
    path = get_dataset_path()
    return {
        "dataset_file": path.name,
        "dataset_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "dependencies": {
            name: version(name)
            for name in (
                "numpy",
                "pandas",
                "scikit-learn",
                "xgboost",
                "joblib",
                "openpyxl",
            )
        },
    }
