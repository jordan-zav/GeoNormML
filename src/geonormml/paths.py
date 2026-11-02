"""Portable user paths and explicit checkout detection, without filesystem writes."""

import os
import sys
from pathlib import Path


def _absolute(value):
    return Path(value).expanduser().resolve()


def get_home():
    """Return the user-owned application directory; never use site-packages."""
    if value := os.getenv("GEONORMML_HOME"):
        return _absolute(value)
    if sys.platform == "win32":
        fallback = Path.home() / "AppData/Local"
        base = Path(os.getenv("LOCALAPPDATA") or fallback)
    elif sys.platform == "darwin":
        fallback = base = Path.home() / "Library/Application Support"
    else:
        fallback = Path.home() / ".local/share"
        base = Path(os.getenv("XDG_DATA_HOME") or fallback)
    if not base.is_absolute():
        base = fallback
    return _absolute(base / "geonormml")


def get_project_root():
    """Use an explicit research root or an actual src checkout; otherwise return None."""
    if value := os.getenv("GEONORMML_PROJECT_ROOT"):
        return _absolute(value)
    candidate = Path(__file__).resolve().parents[2]
    if (candidate / "pyproject.toml").is_file() and (candidate / "src/geonormml/config.py").is_file():
        return candidate
    return None


def get_artifacts_dir():
    if value := os.getenv("GEONORMML_ARTIFACTS_DIR"):
        return _absolute(value)
    return (get_project_root() or get_home()) / "artifacts"


def get_models_dir():
    if value := os.getenv("GEONORMML_MODELS_DIR"):
        return _absolute(value)
    return get_home() / "models"


def get_dataset_dir():
    root = get_project_root()
    return root / "Dataset/Filtered/final" if root else get_home() / "datasets"


def paths_info():
    """Inspect configuration without creating directories or loading resources."""
    root = get_project_root()
    return {
        "home": str(get_home()),
        "project_root": str(root) if root else None,
        "datasets": str(get_dataset_dir()),
        "artifacts": str(get_artifacts_dir()),
        "models": str(get_models_dir()),
    }
