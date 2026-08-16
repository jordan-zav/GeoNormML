from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from .config import DATASET_PATH, DATASET_SHEET, setup_logging

logger = setup_logging("geonormml.data")


def load_training_dataset() -> pd.DataFrame:
    """Load the official training-ready dataset and compute derived features.

    Raises
    ------
    FileNotFoundError
        If ``DATASET_PATH`` does not exist on disk.
    """
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Training dataset not found at:\n  {DATASET_PATH}\n"
            "Ensure the file exists or update DATASET_PATH in geonormml/config.py."
        )

    logger.info("Loading dataset from %s [sheet=%s]", DATASET_PATH.name, DATASET_SHEET)
    df = pd.read_excel(DATASET_PATH, sheet_name=DATASET_SHEET)
    logger.info("Loaded %d samples with %d columns.", len(df), len(df.columns))

    # -----------------------------------------------------------------
    # Derived geochemical features
    # -----------------------------------------------------------------
    if "Alc" not in df.columns and {"Na2O", "K2O"}.issubset(df.columns):
        df["Alc"] = df["Na2O"] + df["K2O"]

    if "Clase_SiO2" not in df.columns and "SiO2" in df.columns:
        df["Clase_SiO2"] = pd.cut(
            df["SiO2"],
            bins=[-float("inf"), 45, 52, 63, float("inf")],
            labels=["Ultramafica", "Basica", "Intermedia", "Acida"],
            right=False,
        )

    if "Serie_Mag" not in df.columns and {"SiO2", "Alc", "Ne", "Le"}.issubset(df.columns):
        df["Serie_Mag"] = "Transicional"
        alkaline_mask = (df["Ne"] >= 1) | (df["Le"] >= 1) | ((df["SiO2"] < 52) & (df["Alc"] >= 5))
        subalkaline_mask = (~alkaline_mask) & ((df["Alc"] < 5) | (df["SiO2"] >= 52))
        df.loc[alkaline_mask, "Serie_Mag"] = "Alcalina"
        df.loc[subalkaline_mask, "Serie_Mag"] = "Subalcalina"

    if "%An en Pl" not in df.columns and {"An", "Ab"}.issubset(df.columns):
        denominator = df["An"] + df["Ab"]
        df["%An en Pl"] = 0.0
        valid = denominator > 0
        df.loc[valid, "%An en Pl"] = (df.loc[valid, "An"] / denominator.loc[valid]) * 100

    if "SUM_QAP" not in df.columns and {"Q", "Or", "Ab", "An"}.issubset(df.columns):
        df["SUM_QAP"] = df["Q"] + df["Or"] + df["Ab"] + df["An"]

    if "SUM_CIPW" not in df.columns:
        cipw_sum_cols = [
            "Q", "Cor", "Or", "Ab", "An", "Le", "Ne", "Kp", "Ac",
            "Di", "Hd", "Wo", "En", "Fs", "Fo", "Fa", "Mt", "Hm",
            "Ilm", "Ru", "Tn", "Ap", "Cc", "Py", "Th", "ns", "ks",
        ]
        present = [col for col in cipw_sum_cols if col in df.columns]
        if present:
            df["SUM_CIPW"] = df[present].sum(axis=1)

    # -----------------------------------------------------------------
    # Petrological indices
    # -----------------------------------------------------------------
    if "ASI" not in df.columns and {"Al2O3", "CaO", "Na2O", "K2O"}.issubset(df.columns):
        mol_Al2O3 = df["Al2O3"] / 101.96
        mol_CaO = df["CaO"].fillna(0) / 56.08
        mol_Na2O = df["Na2O"].fillna(0) / 61.98
        mol_K2O = df["K2O"].fillna(0) / 94.20
        denom_ASI = mol_CaO + mol_Na2O + mol_K2O
        df["ASI"] = 0.0
        valid_ASI = denom_ASI > 0
        df.loc[valid_ASI, "ASI"] = mol_Al2O3.loc[valid_ASI] / denom_ASI.loc[valid_ASI]

    if "Mg_num" not in df.columns and {"MgO", "FeOT"}.issubset(df.columns):
        mol_MgO = df["MgO"] / 40.30
        mol_FeOT = df["FeOT"].fillna(0) / 71.85
        denom_Mg = mol_MgO + mol_FeOT
        df["Mg_num"] = 0.0
        valid_Mg = denom_Mg > 0
        df.loc[valid_Mg, "Mg_num"] = (mol_MgO.loc[valid_Mg] / denom_Mg.loc[valid_Mg]) * 100

    if "DI_Tuttle" not in df.columns:
        felsic_cols = ["Q", "Or", "Ab", "Ne", "Kp", "Le"]
        present_felsic = [col for col in felsic_cols if col in df.columns]
        if present_felsic:
            df["DI_Tuttle"] = df[present_felsic].fillna(0).sum(axis=1)

    if "ICN" not in df.columns:
        mafic_cols = ["Di", "Hd", "Wo", "En", "Fs", "Fo", "Fa", "Mt", "Hm", "Ilm", "Ru"]
        present_mafic = [col for col in mafic_cols if col in df.columns]
        if present_mafic:
            df["ICN"] = df[present_mafic].fillna(0).sum(axis=1)

    # -----------------------------------------------------------------
    # Spatial: approximate distance to Peru trench (vectorised NumPy)
    # -----------------------------------------------------------------
    if "Trench_Dist" not in df.columns and {"LON", "LAT"}.issubset(df.columns):
        df["Trench_Dist"] = _compute_trench_distance(df["LON"].values, df["LAT"].values)
        logger.info("Trench_Dist computed (vectorised). Range: %.1f – %.1f km",
                     df["Trench_Dist"].min(), df["Trench_Dist"].max())

    n_derived = sum(
        1 for c in ["Alc", "Clase_SiO2", "Serie_Mag", "%An en Pl", "SUM_QAP",
                     "SUM_CIPW", "ASI", "Mg_num", "DI_Tuttle", "ICN", "Trench_Dist"]
        if c in df.columns
    )
    logger.info("Feature engineering complete. %d derived columns available.", n_derived)

    return df


# =====================================================================
# Vectorised trench distance (NumPy, ~100× faster than df.apply)
# =====================================================================

# Simplified polyline approximating the Peru–Chile trench axis
_TRENCH_VERTICES = np.array([
    [-82.0,  -4.0],
    [-81.5,  -6.0],
    [-81.0,  -8.0],
    [-80.0, -10.0],
    [-78.5, -12.0],
    [-77.0, -14.0],
    [-75.5, -16.0],
    [-73.5, -18.0],
    [-72.0, -20.0],
], dtype=np.float64)


def _compute_trench_distance(lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    """Vectorised minimum distance from points to the trench polyline.

    Returns distance in approximate kilometres using a flat-earth
    conversion factor of 111.12 km/degree (acceptable for the ~15° span
    of Peru).
    """
    px = np.asarray(lon, dtype=np.float64)
    py = np.asarray(lat, dtype=np.float64)

    n_pts = len(px)
    min_dist = np.full(n_pts, np.inf)

    for i in range(len(_TRENCH_VERTICES) - 1):
        ax, ay = _TRENCH_VERTICES[i]
        bx, by = _TRENCH_VERTICES[i + 1]

        abx = bx - ax
        aby = by - ay
        ab_len_sq = abx ** 2 + aby ** 2

        # Parameter t for projection onto segment [A, B]
        apx = px - ax
        apy = py - ay
        t = (apx * abx + apy * aby) / ab_len_sq
        t = np.clip(t, 0.0, 1.0)

        # Closest point on segment
        cx = ax + t * abx
        cy = ay + t * aby

        dist = np.sqrt((px - cx) ** 2 + (py - cy) ** 2)
        min_dist = np.minimum(min_dist, dist)

    # Convert degrees → km (flat-earth approx, adequate for Peru)
    result = min_dist * 111.12

    # NaN inputs → 0.0 (matches previous behaviour)
    nan_mask = np.isnan(lon) | np.isnan(lat)
    result[nan_mask] = 0.0

    return result
