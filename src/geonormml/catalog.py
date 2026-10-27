"""Version identities shared by publication, export and application clients.

A historical metric is not a substitute for the corresponding trained artifact.
The congress generation and the currently deployed baseline stay distinct.
"""

from copy import deepcopy

CURRENT_GENERATION = "curated_grouped_v2"
LEGACY_GENERATION = "cpg_xxiii_legacy"
CURRENT_MODEL_SPECS = (
    {
        "domain_code": "VOL",
        "domain_name": "volcanic",
        "feature_set": "combined_core",
        "model_name": "XGBoost",
        "model_type": "geochemical_baseline",
    },
    {
        "domain_code": "PLU",
        "domain_name": "plutonic",
        "feature_set": "combined_core",
        "model_name": "RandomForest",
        "model_type": "geochemical_baseline",
    },
)

GENERATION_CATALOG = {
    "schema_version": 1,
    "default_ml_generation": CURRENT_GENERATION,
    "generations": {
        LEGACY_GENERATION: {
            "label": "GeoNormPy / GeoNormML Legacy — CPG XXIII",
            "status": "legacy",
            "presentation": {
                "event": "XXIII Congreso Peruano de Geología",
                "contribution_type": "trabajo técnico",
                "description_es": "Presentado como trabajo técnico en el XXIII Congreso Peruano de Geología.",
                "description_en": "Presented as a technical paper at the XXIII Peruvian Geological Congress.",
            },
            "dataset_rows": 2755,
            "reported_models": [
                {"domain_code": "VOL", "feature_set": "combined_core", "model_name": "XGBoost"},
                {"domain_code": "PLU", "feature_set": "oxides_core", "model_name": "RandomForest"},
            ],
            "metric_source": "accepted_abstract",
            "artifact_status": "original_congress_estimators_not_located",
            "inference_available": False,
            "warning": "Historical publication; current estimators must not be relabelled as the congress models.",
        },
        CURRENT_GENERATION: {
            "label": "GeoNormML — baseline curado con validación por grupos",
            "status": "current",
            "dataset_rows": 2755,
            "models": list(CURRENT_MODEL_SPECS),
            "metric_source": "validation/baseline_validation.json",
            "validation": "grouped_training_cv_and_reserved_holdout",
            "geospatial_predictors": False,
            "cipw_training_contract": {
                "status": "historical_not_recorded",
                "profile": None,
                "engine_version": None,
                "warning": "Do not replace stored normative features with another profile without revalidation.",
            },
        },
    },
    "geonormpy": {
        "previous_release": {"label": "GeoNormPy Legacy", "version": "1.0.0", "status": "legacy"},
        "congress_advertised_release": "0.1.1",
        "revised_code_version": "1.1.0",
        "profiles": {
            "extended_cipw_v3": {
                "label": "Compatibilidad Legacy (corregida)",
                "profile_version": "3.1",
                "exact_previous_release": False,
            },
            "verma2003": {"label": "Verma 2003", "profile_version": "1.0"},
            "pruseth2009": {"label": "Pruseth 2009", "profile_version": "1.0"},
        },
        "new_profiles_ml_status": "experimental_not_promoted",
    },
}


def generation_catalog():
    """Return detached metadata, safe for JSON/API clients to annotate."""
    return deepcopy(GENERATION_CATALOG)


def is_current_official_model(domain, feature_set, model_name):
    return any(
        spec["domain_code"] == domain and spec["feature_set"] == feature_set and spec["model_name"] == model_name
        for spec in CURRENT_MODEL_SPECS
    )
