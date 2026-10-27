"""Public publication settings must match the evidence and evaluation scope."""

import json
from pathlib import Path

from geonormml.catalog import CURRENT_GENERATION, generation_catalog

CONFIG = Path(__file__).resolve().parents[1] / "poster_cpg23/configs"


def read(name):
    return json.loads((CONFIG / name).read_text(encoding="utf-8"))


def test_evidence_keeps_legacy_and_current_generation_separate():
    evidence = read("current_baseline.evidence.json")
    assert evidence["generation_id"] == CURRENT_GENERATION
    assert evidence["generation_catalog"] == generation_catalog()
    assert evidence["rows"] == sum(evidence["domain_counts"].values()) == 2755
    assert sum(m["holdout_rows"] for m in evidence["models"]) == 553
    assert sum(m["training_rows"] + m["holdout_rows"] for m in evidence["models"]) == 2755


def test_current_publication_cards_use_training_cv_instead_of_legacy_numbers():
    evidence = read("current_baseline.evidence.json")
    editorial = read("geonorm_editorial.json")["poster"]
    slides = read("geonormpy_geonormml.json")
    assert editorial["generation_id"] == slides["generation_id"] == evidence["generation_id"]
    for index, model in enumerate(evidence["models"]):
        expected = [f'{model["cv"][key]:.3f}' for key in ("CA", "AUC_macro_ovr", "MCC")]
        assert [m["value"] for m in editorial["results"][index]["metrics"]] == expected
        assert [m["value"] for m in slides["slides"][4 + index]["metrics"]] == expected
        assert "CV" in editorial["results"][index]["metrics"][0]["label"]
        assert "holdout" in editorial["results"][index]["caption"]
        assert "artifacts/validation/" in editorial["results"][index]["visual"]


def test_legacy_generators_require_explicit_historical_reproduction():
    root = CONFIG.parent
    for filename in ("build_geonorm_totem_v1.py", "build_geonorm_totem_illustrator.jsx"):
        code = (root / filename).read_text(encoding="utf-8")
        assert "GEONORMML_ALLOW_LEGACY_POSTER" in code
        assert "Legacy_Totem_GeoNorm_CPG_XXIII" in code
