from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

OXIDE_FEATURES_CORE = [
    "SiO2",
    "TiO2",
    "Al2O3",
    "FeOT",
    "CaO",
    "MgO",
    "MnO",
    "K2O",
    "Na2O",
    "P2O5",
    "LOI",
    "Sum_Oxs",
]

OXIDE_FEATURES_EXTENDED = [
    *OXIDE_FEATURES_CORE,
    "CO2",
    "F",
    "Cl",
    "SO3",
    "S",
]

CIPW_DERIVED_FEATURES = [
    "%An en Pl",
    "SUM_QAP",
    "SUM_CIPW",
    "ASI",
    "Mg_num",
    "DI_Tuttle",
    "ICN",
]

PETROCHEM_CONTEXT_FEATURES = [
    "Clase_SiO2",
    "Serie_Mag",
]

CIPW_FEATURES = [
    "Q",
    "Cor",
    "Or",
    "Ab",
    "An",
    "Le",
    "Ne",
    "Kp",
    "Ac",
    "Di",
    "Hd",
    "Wo",
    "En",
    "Fs",
    "Fo",
    "Fa",
    "Mt",
    "Hm",
    "Ilm",
    "Ru",
    "Tn",
    "Ap",
    "Cc",
    "Py",
    "Th",
    "ns",
    "ks",
]

SPATIAL_FEATURES = [
    "Trench_Dist",
    "LAT",
]

# Features produced by spatial_join_dataset.py (require INGEMMET shapefiles)
GEODATA_FEATURES = [
    "Fault_Dist",
    "Geol_Unit",
    "Geol_Age_100k",
    "UTM_Zone",
    "Metal_Belt",
]

CONTEXT_FEATURES = [
    "ROCK TYPE",
]


@dataclass(frozen=True)
class FeatureSet:
    name: str
    columns: list[str]


FEATURE_SETS = {
    "oxides_core": FeatureSet(name="oxides_core", columns=OXIDE_FEATURES_CORE),
    "oxides": FeatureSet(name="oxides", columns=OXIDE_FEATURES_EXTENDED),
    "cipw": FeatureSet(name="cipw", columns=CIPW_FEATURES),
    "combined_core": FeatureSet(name="combined_core", columns=OXIDE_FEATURES_CORE + CIPW_FEATURES),
    "combined": FeatureSet(name="combined", columns=OXIDE_FEATURES_EXTENDED + CIPW_FEATURES),
    "oxides_contextual": FeatureSet(
        name="oxides_contextual",
        columns=OXIDE_FEATURES_CORE + PETROCHEM_CONTEXT_FEATURES,
    ),
    "combined_contextual": FeatureSet(
        name="combined_contextual",
        columns=OXIDE_FEATURES_CORE + CIPW_FEATURES + PETROCHEM_CONTEXT_FEATURES,
    ),
    "combined_enriched": FeatureSet(
        name="combined_enriched",
        columns=OXIDE_FEATURES_CORE + CIPW_FEATURES + CIPW_DERIVED_FEATURES,
    ),
    "combined_enriched_spatial": FeatureSet(
        name="combined_enriched_spatial",
        columns=OXIDE_FEATURES_CORE + CIPW_FEATURES + CIPW_DERIVED_FEATURES + SPATIAL_FEATURES,
    ),
    # --- New sets (require spatial_join_dataset.py output) ---
    "combined_enriched_geodata": FeatureSet(
        name="combined_enriched_geodata",
        columns=(OXIDE_FEATURES_CORE + CIPW_FEATURES + CIPW_DERIVED_FEATURES + SPATIAL_FEATURES + GEODATA_FEATURES),
    ),
    "combined_full": FeatureSet(
        name="combined_full",
        columns=(
            OXIDE_FEATURES_CORE
            + CIPW_FEATURES
            + CIPW_DERIVED_FEATURES
            + SPATIAL_FEATURES
            + GEODATA_FEATURES
            + PETROCHEM_CONTEXT_FEATURES
        ),
    ),
}


def validate_feature_columns(df: pd.DataFrame) -> dict[str, list[str]]:
    """Return missing columns per feature set, if any."""
    missing: dict[str, list[str]] = {}
    for key, feature_set in FEATURE_SETS.items():
        missing_cols = [column for column in feature_set.columns if column not in df.columns]
        if missing_cols:
            missing[key] = missing_cols
    return missing
