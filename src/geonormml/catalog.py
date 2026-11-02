"""Version identities shared by publication, export and application clients.

A historical metric is not a substitute for the corresponding trained artifact.
Historical export identities are preserved separately from operational adoption.
"""

from copy import deepcopy

CURRENT_GENERATION = "curated_grouped_v2"
LEGACY_GENERATION = "cpg_xxiii_legacy"
OPERATIONAL_GENERATION = "partition_stability_v5_20261027"
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


OPERATIONAL_ADOPTION = {
    "generation_id": OPERATIONAL_GENERATION,
    "application": "PetroPyQAPF",
    "decision_date": "2026-10-27",
    "status": "operational_adoption_external_evaluation_pending",
    "eligible_samples": {"VOL": 1725, "PLU": 976},
    "models": [
        {
            "domain_code": "VOL",
            "model_name": "HistGradientBoosting",
            "variant": "balanced15",
            "feature_count": 12,
            "cipw_profile": None,
        },
        {
            "domain_code": "PLU",
            "model_name": "RandomForest",
            "variant": "reference_leaf3",
            "feature_count": 41,
            "cipw_profile": "verma2003",
            "cipw_profile_version": "1.0",
            "engine_version": "1.1.0",
            "iron_policy": "fixed",
            "fe3_fraction": 0.15,
            "carbonate_mode": "calcite",
            "apatite_feature": "Ap + FAp",
        },
    ],
    "selector_internal_macro_f1": {"VOL": 0.635, "PLU": 0.389},
    "metric_scope": "internal_selection_procedure_not_external_final_model_evaluation",
    "external_evaluation": "pending",
    "probability_calibration": "not_externally_demonstrated",
    "artifacts_in_repository": False,
    "historical_export_defaults_changed": False,
    "decision_document": "docs/revisiones/adopcion_petropyqapf_v5_20261027.md",
}


def generation_catalog(*, include_operational=False):
    """Return detached metadata; preserve the historical publication snapshot by default.

    Opt in to operational adoption metadata without changing frozen export identities.
    """
    result = deepcopy(GENERATION_CATALOG)
    if include_operational:
        result["default_scope"] = "historical_export_pipeline_not_petropyqapf_operational_default"
        result["operational_adoption"] = deepcopy(OPERATIONAL_ADOPTION)
        result["geonormpy"]["new_profiles_ml_status"] = "verma2003_operational_in_v5_external_evaluation_pending"
    return result


def is_current_official_model(domain, feature_set, model_name):
    return any(
        spec["domain_code"] == domain and spec["feature_set"] == feature_set and spec["model_name"] == model_name
        for spec in CURRENT_MODEL_SPECS
    )
