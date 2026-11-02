"""Explicit model manifests, portable discovery and trusted artifact loading."""

import hashlib
import io
import json
import platform
from copy import deepcopy
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path, PurePosixPath, PureWindowsPath

from .paths import get_models_dir

FORMAT = "geonormml-model-bundle"
REQUIRED_DEPENDENCIES = ("scikit-learn", "numpy", "scipy", "joblib")
CALIBRATION_NOTE = "Model probabilities are not certified individual confidence or externally calibrated by this API."


class ModelError(ValueError):
    """An actionable contract or inference failure, suitable for JSON clients."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code

    def to_dict(self):
        return {"code": self.code, "message": str(self)}


def runtime_dependencies():
    """Versions for a new artifact; do not use these to guess an old model's environment."""
    return {name: version(name) for name in (*REQUIRED_DEPENDENCIES, "xgboost")}


def _sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_manifest(path):
    path = Path(path).expanduser()
    if path.is_dir():
        path = path / "manifest.json"
    elif not path.exists() and len(path.parts) == 1 and path.suffix != ".json":
        root = get_models_dir()
        path = root / path / "manifest.json"
    return path.resolve()


def _strings(value, name):
    if not isinstance(value, list) or not value or any(not isinstance(v, str) or not v for v in value):
        raise ModelError("invalid_manifest", f"{name} must be a nonempty list of names")
    if len(set(value)) != len(value):
        raise ModelError("invalid_manifest", f"{name} contains duplicate names")


def validate_manifest(document):
    if not isinstance(document, dict) or document.get("format") != FORMAT or document.get("schema_version") != 1:
        raise ModelError("invalid_manifest", "Expected geonormml-model-bundle schema version 1")
    for name in ("generation_id", "python_version"):
        if not isinstance(document.get(name), str) or not document[name]:
            raise ModelError("invalid_manifest", f"Missing {name}")
    pieces = document["python_version"].split(".")
    if len(pieces) != 2 or not all(piece.isdigit() for piece in pieces):
        raise ModelError("invalid_manifest", "python_version must contain major.minor, for example 3.11")
    if document.get("domain_code") not in ("VOL", "PLU"):
        raise ModelError("invalid_manifest", "domain_code must be VOL or PLU")
    for name in ("feature_columns", "classes"):
        _strings(document.get(name), name)
    if document.get("prediction_encoding", "encoded") not in ("encoded", "labels"):
        raise ModelError("invalid_manifest", "prediction_encoding must be encoded or labels")
    mode = document.get("input_mode")
    if mode not in ("prepared_features", "oxide_chemistry"):
        raise ModelError("invalid_manifest", "Declare prepared_features or oxide_chemistry input_mode")
    categories = document.get("categorical_columns", [])
    if (
        not isinstance(categories, list)
        or any(not isinstance(c, str) for c in categories)
        or any(c not in document["feature_columns"] for c in categories)
        or len(set(categories)) != len(categories)
    ):
        raise ModelError("invalid_manifest", "categorical_columns must be a subset of feature_columns")
    dependencies = document.get("dependencies")
    if not isinstance(dependencies, dict) or any(not dependencies.get(p) for p in REQUIRED_DEPENDENCIES):
        raise ModelError("invalid_manifest", "Record exact scikit-learn, numpy, scipy and joblib versions")
    if any(not isinstance(k, str) or not isinstance(v, str) or not v for k, v in dependencies.items()):
        raise ModelError("invalid_manifest", "Dependency versions must be strings")
    relative = document.get("model_file")
    if not isinstance(relative, str) or not relative or "\\" in relative or "\x00" in relative:
        raise ModelError("invalid_manifest", "model_file must be a portable relative path")
    parts = PurePosixPath(relative)
    if parts.is_absolute() or PureWindowsPath(relative).drive or ".." in parts.parts:
        raise ModelError("invalid_manifest", "model_file must stay inside the manifest directory")
    if parts.suffix.lower() != ".joblib":
        raise ModelError("invalid_manifest", "model_file must name a .joblib artifact")
    digest = document.get("model_sha256")
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ModelError("invalid_manifest", "model_sha256 must be a lowercase SHA-256 digest")
    if mode == "prepared_features" and document.get("normative") is not None:
        raise ModelError("invalid_manifest", "Prepared features must not request normative recomputation")
    if mode == "oxide_chemistry":
        from .features import FEATURE_SETS

        family = document.get("feature_set")
        allowed = {"oxides_core", "combined_core", "combined_contextual", "combined_enriched"}
        if family not in allowed or document["feature_columns"] != FEATURE_SETS[family].columns:
            raise ModelError("invalid_manifest", "Unsupported or inconsistent chemistry feature_set and column order")
        if family == "oxides_core" and document.get("normative") is not None:
            raise ModelError("invalid_manifest", "The oxide-only model must not request normative recomputation")
        if family != "oxides_core":
            contract = document.get("normative", {})
            if not isinstance(contract, dict):
                raise ModelError("invalid_manifest", "normative must be a contract object")
            if (
                contract.get("engine_version") != "1.1.0"
                or contract.get("profile") not in ("extended_cipw_v3", "verma2003", "pruseth2009")
                or contract.get("profile_version")
                != ("3.1" if contract.get("profile") == "extended_cipw_v3" else "1.0")
                or contract.get("iron_policy") != "fixed"
                or contract.get("carbonate_mode") != "calcite"
                or contract.get("apatite_feature") != "Ap + FAp"
            ):
                raise ModelError("invalid_manifest", "Declare the supported fixed-FeOT normative contract explicitly")
            fraction = contract.get("fe3_fraction")
            if isinstance(fraction, bool) or not isinstance(fraction, (int, float)) or not 0 <= fraction <= 1:
                raise ModelError("invalid_manifest", "fe3_fraction must be finite and between zero and one")
    return document


def read_manifest(path):
    path = resolve_manifest(path)
    try:
        if path.stat().st_size > 1024 * 1024:
            raise ModelError("invalid_manifest", "Manifest exceeds 1 MiB")
        document = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ModelError("manifest_unreadable", f"Cannot read manifest {path}: {error}") from error
    return path, validate_manifest(document)


def _model_path(manifest, document):
    path = (manifest.parent / document["model_file"]).resolve()
    if not path.is_relative_to(manifest.parent):
        raise ModelError("invalid_manifest", "Resolved model path escapes the manifest directory")
    return path


def _check_environment(document):
    if document["python_version"] != ".".join(platform.python_version_tuple()[:2]):
        raise ModelError("environment_mismatch", "Use the recorded Python major/minor version")
    for name, expected in document["dependencies"].items():
        try:
            actual = version(name)
        except PackageNotFoundError as error:
            raise ModelError("environment_mismatch", f"Missing dependency {name}=={expected}") from error
        if actual != expected:
            raise ModelError("environment_mismatch", f"Expected {name}=={expected}; installed {actual}")
    if document.get("normative"):
        try:
            from geonormpy import __version__

            installed = version("geonormpy")
        except (ImportError, PackageNotFoundError) as error:
            raise ModelError(
                "environment_mismatch", "GeoNormPy 1.1.0 is required for this normative contract"
            ) from error

        if __version__ != installed or __version__ != document["normative"]["engine_version"]:
            raise ModelError("environment_mismatch", "The normative engine differs from the input contract")


def inspect_model(path, *, verify=True):
    """Read JSON metadata and optionally check bytes/environment, without deserialization."""
    manifest, document = read_manifest(path)
    model_path = _model_path(manifest, document)
    if verify:
        _check_environment(document)
        try:
            digest = _sha256_file(model_path)
        except OSError as error:
            raise ModelError("model_unreadable", str(error)) from error
        if digest != document["model_sha256"]:
            raise ModelError("checksum_mismatch", "Model bytes do not match the manifest")
    return {
        "manifest_path": str(manifest),
        "model_path": str(model_path),
        "verified": verify,
        "generation_id": document["generation_id"],
        "domain_code": document["domain_code"],
        "input_mode": document["input_mode"],
        "features": document["feature_columns"],
        "classes": document["classes"],
        "dependencies": document["dependencies"],
        "normative": document.get("normative"),
        "note": CALIBRATION_NOTE,
    }


def list_models(directory=None):
    """List metadata from the explicit registry, without loading any model objects."""
    root = Path(directory).expanduser().resolve() if directory is not None else get_models_dir()
    records = []
    for manifest in sorted({*root.glob("*.json"), *root.glob("*/manifest.json")}):
        try:
            records.append({"status": "available", **inspect_model(manifest, verify=False)})
        except ModelError as error:
            records.append({"status": "invalid", "manifest_path": str(manifest), "error": error.to_dict()})
    return records


def create_model_manifest(model_file, metadata, *, output=None):
    """Attach an explicit known training contract; never infer it by loading the artifact."""
    model_file = Path(model_file).expanduser().resolve(strict=True)
    destination = Path(output).expanduser().resolve() if output else model_file.parent / "manifest.json"
    if not model_file.is_relative_to(destination.parent):
        raise ModelError("invalid_manifest", "Place the manifest alongside or above the model artifact")
    document = {
        **metadata,
        "format": FORMAT,
        "schema_version": 1,
        "model_file": model_file.relative_to(destination.parent).as_posix(),
        "model_sha256": _sha256_file(model_file),
    }
    validate_manifest(document)
    text = json.dumps(document, indent=2, allow_nan=False) + "\n"
    with destination.open("x", encoding="utf-8") as stream:
        stream.write(text)
    return destination


@dataclass(frozen=True)
class LoadedModel:
    _document: dict
    estimator: object

    @property
    def manifest(self):
        return deepcopy(self._document)

    def predict(self, data, *, id_column=None):
        from .inference import predict_frame

        return predict_frame(data, self, id_column=id_column)


def load_model(path, *, trusted=False):
    """Load only explicitly trusted joblib bundles after contract and hash checks."""
    if not trusted:
        raise ModelError(
            "trust_required", "Loading joblib can execute code; load only a trusted model with trusted=True"
        )
    manifest, document = read_manifest(path)
    _check_environment(document)
    try:
        data = _model_path(manifest, document).read_bytes()
    except OSError as error:
        raise ModelError("model_unreadable", str(error)) from error
    if hashlib.sha256(data).hexdigest() != document["model_sha256"]:
        raise ModelError("checksum_mismatch", "Model bytes do not match the manifest")
    try:
        import joblib

        bundle = joblib.load(io.BytesIO(data))
    except Exception as error:
        raise ModelError("model_load_failed", str(error)) from error
    if not isinstance(bundle, dict) or "estimator" not in bundle:
        raise ModelError("bundle_mismatch", "Expected a mapping containing estimator and its training contract")
    selected = bundle.get("selected")
    columns = bundle.get("feature_columns", selected.get("columns") if isinstance(selected, dict) else None)
    if hasattr(columns, "tolist"):
        columns = columns.tolist()
    if (
        not isinstance(columns, (list, tuple))
        or list(columns) != document["feature_columns"]
        or bundle.get("generation_id") != document["generation_id"]
    ):
        raise ModelError("bundle_mismatch", "Feature order or generation differs between artifact and manifest")
    columns = list(columns)
    if "domain_code" in bundle and bundle["domain_code"] != document["domain_code"]:
        raise ModelError("bundle_mismatch", "Artifact and manifest domains differ")
    if document["input_mode"] == "oxide_chemistry":
        if (
            bundle.get("input_mode") != "oxide_chemistry"
            or bundle.get("feature_set") != document["feature_set"]
            or bundle.get("normative") != document.get("normative")
        ):
            raise ModelError(
                "bundle_mismatch",
                "Raw chemistry requires the same explicit contract inside the artifact; "
                "use prepared_features for legacy bundles",
            )
    labels = bundle.get("classes")
    if labels is None and "label_encoder" in bundle:
        labels = getattr(bundle["label_encoder"], "classes_", None)
    if hasattr(labels, "tolist"):
        labels = labels.tolist()
    if not isinstance(labels, (list, tuple)) or list(labels) != document["classes"]:
        raise ModelError("bundle_mismatch", "Artifact and manifest class labels differ")
    estimator = bundle["estimator"]
    labels = list(labels)
    expected = list(range(len(labels))) if document.get("prediction_encoding", "encoded") == "encoded" else labels
    if not hasattr(estimator, "predict") or list(getattr(estimator, "classes_", [])) != expected:
        raise ModelError("bundle_mismatch", "Estimator classes or prediction interface differ from the manifest")
    if hasattr(estimator, "feature_names_in_") and list(estimator.feature_names_in_) != columns:
        raise ModelError("bundle_mismatch", "Estimator feature names differ from the declared order")
    if getattr(estimator, "n_features_in_", len(columns)) != len(columns):
        raise ModelError("bundle_mismatch", "Estimator feature count differs from the declared contract")
    return LoadedModel(document, estimator)
