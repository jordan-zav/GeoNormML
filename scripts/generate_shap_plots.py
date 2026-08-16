from __future__ import annotations

import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

from geonormml.config import ARTIFACTS_DIR, RANDOM_STATE, ROCK_TYPE_COLUMN, TARGET_COLUMN, setup_logging
from geonormml.data import load_training_dataset
from geonormml.features import FEATURE_SETS

logger = setup_logging("generate_shap_plots")

SHAP_DIR = ARTIFACTS_DIR / "shap_interpretation"


def main() -> None:
    SHAP_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Loading training dataset...")
    df = load_training_dataset()

    feature_set_name = "combined_enriched_spatial"
    feature_columns = FEATURE_SETS[feature_set_name].columns

    # =========================================================================
    # 1. DOMINIO VOLCÁNICO (VOL) - XGBoost
    # =========================================================================
    logger.info("--- Processing Volcanic Domain (VOL) ---")
    vol_df = df[df[ROCK_TYPE_COLUMN] == "VOL"].copy()
    
    X_vol_raw = vol_df[feature_columns]
    y_vol_raw = vol_df[TARGET_COLUMN]

    imputer_vol = SimpleImputer(strategy="median")
    X_vol = pd.DataFrame(imputer_vol.fit_transform(X_vol_raw), columns=feature_columns)

    le_vol = LabelEncoder()
    y_vol = le_vol.fit_transform(y_vol_raw)
    class_names_vol = le_vol.classes_.tolist()

    logger.info("Training RandomForest model for VOL...")
    rf_model_vol = RandomForestClassifier(
        n_estimators=150,
        random_state=RANDOM_STATE,
        class_weight="balanced",
        n_jobs=-1,
    )
    rf_model_vol.fit(X_vol, y_vol)

    logger.info("Calculating SHAP values for VOL...")
    explainer_vol = shap.TreeExplainer(rf_model_vol)
    shap_values_vol = explainer_vol.shap_values(X_vol)

    # 1.1 Global Bar Plot
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values_vol, X_vol, plot_type="bar", class_names=class_names_vol, show=False)
    plt.title("Rocas volcánicas: importancia global de variables (SHAP)")
    plt.tight_layout()
    bar_path_vol = SHAP_DIR / "volcanic_shap_bar.png"
    plt.savefig(bar_path_vol, dpi=200)
    plt.close()
    logger.info("Saved: %s", bar_path_vol)

    # 1.2 Detailed Beeswarm Plot for 'riolita' if present
    target_class_vol = "riolita"
    if target_class_vol in class_names_vol:
        idx = class_names_vol.index(target_class_vol)
        plt.figure(figsize=(10, 8))
        # Para modelos multi-clase en SHAP, shap_values es una lista o array 3D.
        # Si es una lista de arrays: shap_values[idx]
        # Si es un array 3D: shap_values[:, :, idx]
        if isinstance(shap_values_vol, list):
            class_shap = shap_values_vol[idx]
        else:
            class_shap = shap_values_vol[:, :, idx] if len(shap_values_vol.shape) == 3 else shap_values_vol
            
        shap.summary_plot(class_shap, X_vol, show=False)
        plt.title(f"Dominio volcánico: variables SHAP para '{target_class_vol.capitalize()}'")
        plt.tight_layout()
        beeswarm_path_vol = SHAP_DIR / f"volcanic_shap_detail_{target_class_vol}.png"
        plt.savefig(beeswarm_path_vol, dpi=200)
        plt.close()
        logger.info("Saved: %s", beeswarm_path_vol)

    # =========================================================================
    # 2. DOMINIO PLUTÓNICO (PLU) - RandomForest
    # =========================================================================
    logger.info("--- Processing Plutonic Domain (PLU) ---")
    plu_df = df[df[ROCK_TYPE_COLUMN] == "PLU"].copy()
    
    X_plu_raw = plu_df[feature_columns]
    y_plu_raw = plu_df[TARGET_COLUMN]

    imputer_plu = SimpleImputer(strategy="median")
    X_plu = pd.DataFrame(imputer_plu.fit_transform(X_plu_raw), columns=feature_columns)

    le_plu = LabelEncoder()
    y_plu = le_plu.fit_transform(y_plu_raw)
    class_names_plu = le_plu.classes_.tolist()

    logger.info("Training RandomForest model for PLU...")
    rf_model = RandomForestClassifier(
        n_estimators=150,
        random_state=RANDOM_STATE,
        class_weight="balanced",
        n_jobs=-1,
    )
    rf_model.fit(X_plu, y_plu)

    logger.info("Calculating SHAP values for PLU...")
    explainer_plu = shap.TreeExplainer(rf_model)
    shap_values_plu = explainer_plu.shap_values(X_plu)

    # 2.1 Global Bar Plot
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values_plu, X_plu, plot_type="bar", class_names=class_names_plu, show=False)
    plt.title("Rocas plutónicas: importancia global de variables (SHAP)")
    plt.tight_layout()
    bar_path_plu = SHAP_DIR / "plutonic_shap_bar.png"
    plt.savefig(bar_path_plu, dpi=200)
    plt.close()
    logger.info("Saved: %s", bar_path_plu)

    # 2.2 Detailed Beeswarm Plot for 'granito' if present
    target_class_plu = "granito"
    if target_class_plu in class_names_plu:
        idx = class_names_plu.index(target_class_plu)
        plt.figure(figsize=(10, 8))
        if isinstance(shap_values_plu, list):
            class_shap = shap_values_plu[idx]
        else:
            class_shap = shap_values_plu[:, :, idx] if len(shap_values_plu.shape) == 3 else shap_values_plu
            
        shap.summary_plot(class_shap, X_plu, show=False)
        plt.title(f"Dominio plutónico: variables SHAP para '{target_class_plu.capitalize()}'")
        plt.tight_layout()
        beeswarm_path_plu = SHAP_DIR / f"plutonic_shap_detail_{target_class_plu}.png"
        plt.savefig(beeswarm_path_plu, dpi=200)
        plt.close()
        logger.info("Saved: %s", beeswarm_path_plu)

    logger.info("SHAP analysis successfully completed! Check plots in: %s", SHAP_DIR)


if __name__ == "__main__":
    main()
