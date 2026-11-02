"""Core utilities for the GeoNormML modeling pipeline."""

from ._version import __version__
from .models import ModelError, create_model_manifest, inspect_model, list_models, load_model

__all__ = [
    "__version__",
    "ModelError",
    "load_model",
    "inspect_model",
    "list_models",
    "create_model_manifest",
    "predict",
]


def predict(data, model, *, trusted=False, id_column=None):
    """Run explicit, row-preserving inference; see the installed API guide."""
    from .inference import predict as run

    return run(data, model, trusted=trusted, id_column=id_column)
