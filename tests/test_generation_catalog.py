from geonormml.catalog import CURRENT_GENERATION, LEGACY_GENERATION, generation_catalog
from scripts.export_transfer_bundle_models import model_policy


def test_legacy_congress_models_do_not_masquerade_as_current_artifacts():
    catalog = generation_catalog()
    legacy = catalog["generations"][LEGACY_GENERATION]
    assert legacy["status"] == "legacy" and not legacy["inference_available"]
    assert legacy["presentation"]["contribution_type"] == "trabajo técnico"
    assert "XXIII Congreso Peruano" in legacy["presentation"]["event"]
    assert legacy["reported_models"][1]["feature_set"] == "oxides_core"
    current = catalog["generations"][CURRENT_GENERATION]
    assert all(spec["feature_set"] == "combined_core" for spec in current["models"])
    assert current["cipw_training_contract"]["profile"] is None


def test_legacy_engine_is_not_identical_to_corrected_compatibility_profile():
    engine = generation_catalog()["geonormpy"]
    assert engine["previous_release"]["status"] == "legacy"
    assert engine["previous_release"]["version"] == "1.0.0"
    assert not engine["profiles"]["extended_cipw_v3"]["exact_previous_release"]
    assert engine["new_profiles_ml_status"] == "experimental_not_promoted"


def test_catalog_callers_cannot_change_shared_generation_identity():
    catalog = generation_catalog()
    catalog["generations"][LEGACY_GENERATION]["status"] = "current"
    assert generation_catalog()["generations"][LEGACY_GENERATION]["status"] == "legacy"


def test_only_the_selected_domain_algorithm_pairs_are_official():
    assert model_policy("VOL", "combined_core", "XGBoost")["status"] == "official"
    assert model_policy("PLU", "combined_core", "RandomForest")["status"] == "official"
    assert model_policy("PLU", "oxides_core", "RandomForest")["status"] == "secondary"
    assert model_policy("VOL", "combined_core", "RandomForest")["status"] == "secondary"
    assert model_policy("PLU", "combined_enriched", "XGBoost")["status"] == "secondary"
    assert model_policy("VOL", "combined_enriched_spatial", "XGBoost")["status"] == "experimental"
