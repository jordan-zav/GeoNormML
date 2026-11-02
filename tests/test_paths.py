"""Installed defaults stay in user-owned storage; checkout compatibility is explicit."""

from pathlib import Path

from geonormml import paths


def test_installed_paths_never_default_to_python_or_create_directories(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "__file__", str(tmp_path / "python/Lib/site-packages/geonormml/paths.py"))
    home = tmp_path / "user space"
    monkeypatch.setenv("GEONORMML_HOME", str(home))
    monkeypatch.delenv("GEONORMML_PROJECT_ROOT", raising=False)
    monkeypatch.delenv("GEONORMML_ARTIFACTS_DIR", raising=False)
    monkeypatch.delenv("GEONORMML_MODELS_DIR", raising=False)
    assert paths.get_project_root() is None
    assert paths.get_artifacts_dir() == home / "artifacts"
    assert paths.get_dataset_dir() == home / "datasets"
    assert paths.get_models_dir() == home / "models"
    assert paths.paths_info()["project_root"] is None
    assert not home.exists()


def test_explicit_paths_are_dynamic_and_absolute(tmp_path, monkeypatch):
    for variable, getter in [
        ("GEONORMML_HOME", paths.get_home),
        ("GEONORMML_ARTIFACTS_DIR", paths.get_artifacts_dir),
        ("GEONORMML_MODELS_DIR", paths.get_models_dir),
    ]:
        path = tmp_path / variable
        monkeypatch.setenv(variable, str(path))
        assert getter() == path
        monkeypatch.setenv(variable, str(path / "changed"))
        assert getter() == path / "changed"
    monkeypatch.setenv("GEONORMML_PROJECT_ROOT", str(tmp_path / "research"))
    assert paths.get_project_root() == tmp_path / "research"
    assert paths.get_dataset_dir() == tmp_path / "research/Dataset/Filtered/final"
    assert isinstance(paths.get_models_dir(), Path)
