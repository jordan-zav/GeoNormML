"""Genera el dashboard compacto de confiabilidad de GeoNormML + GeoNormPy.

Las metricas ML se leen del ranking vigente, el balance CIPW se calcula desde
el dataset oficial y el estado de GeoNormPy se obtiene ejecutando sus pruebas.
"""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
RANKING_PATH = (
    ARTIFACTS_DIR
    / "ml_benchmark"
    / "figuras_resumen"
    / "ranking_configuraciones.csv"
)
DATASET_PATH = (
    PROJECT_ROOT
    / "Dataset"
    / "Filtered"
    / "final"
    / "Merge_Filtered_training_ready_v5_spatial.xlsx"
)
OUTPUT_PATH = ARTIFACTS_DIR / "dashboard_confiabilidad_actualizado.png"


def spatial_metrics() -> dict[str, float]:
    """Lee exactitud y MCC de los dos modelos espaciales oficiales."""
    ranking = pd.read_csv(RANKING_PATH)
    selected = ranking[
        (ranking["modelo"] == "XGBoost")
        & (ranking["feature_set"] == "combined_enriched_spatial")
    ].set_index("domain")

    missing = {"VOL", "PLU"} - set(selected.index)
    if missing:
        raise ValueError(f"Faltan dominios espaciales en el ranking: {sorted(missing)}")

    return {
        "Exactitud espacial · VOL": float(selected.loc["VOL", "CA"]),
        "MCC espacial · VOL": float(selected.loc["VOL", "MCC"]),
        "Exactitud espacial · PLU": float(selected.loc["PLU", "CA"]),
        "MCC espacial · PLU": float(selected.loc["PLU", "MCC"]),
    }


def cipw_balance_score() -> tuple[float, int]:
    """Calcula la fraccion con error de balance de masa <= 0.10."""
    data = pd.read_excel(
        DATASET_PATH,
        sheet_name="training_ready_final",
        usecols=["mass_balance_error"],
    )
    errors = pd.to_numeric(data["mass_balance_error"], errors="coerce")
    if errors.isna().any():
        raise ValueError("El dataset contiene balances CIPW ausentes o no numericos")
    return float((errors <= 0.10).mean()), len(errors)


def geonormpy_test_score() -> tuple[float, int, int]:
    """Ejecuta pytest y devuelve proporcion aprobada, aprobadas y total."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=PROJECT_ROOT.parent / "GeoNormPy",
        capture_output=True,
        text=True,
        check=False,
    )
    output = f"{result.stdout}\n{result.stderr}"
    passed_match = re.search(r"(\d+) passed", output)
    failed_match = re.search(r"(\d+) failed", output)
    error_match = re.search(r"(\d+) errors?", output)
    passed = int(passed_match.group(1)) if passed_match else 0
    failed = int(failed_match.group(1)) if failed_match else 0
    errors = int(error_match.group(1)) if error_match else 0
    total = passed + failed + errors
    if total == 0:
        raise RuntimeError(f"No se pudo interpretar el resultado de pytest:\n{output}")
    return passed / total, passed, total


def create_dashboard() -> Path:
    """Compone y guarda el dashboard en formato PNG."""
    metrics = spatial_metrics()
    cipw_score, sample_count = cipw_balance_score()
    test_score, tests_passed, tests_total = geonormpy_test_score()

    labels = [
        "MCC espacial · PLU",
        "Exactitud espacial · PLU",
        "MCC espacial · VOL",
        "Exactitud espacial · VOL",
        "Balance CIPW · error ≤ 0.10",
        "Pruebas GeoNormPy",
    ]
    values = [
        metrics["MCC espacial · PLU"],
        metrics["Exactitud espacial · PLU"],
        metrics["MCC espacial · VOL"],
        metrics["Exactitud espacial · VOL"],
        cipw_score,
        test_score,
    ]
    colors = ["#B66A4A", "#B66A4A", "#287C8E", "#287C8E", "#4C956C", "#4C956C"]

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 12,
            "axes.titleweight": "bold",
        }
    )
    fig, ax = plt.subplots(figsize=(13.5, 8), facecolor="#F7F7F4")
    ax.set_facecolor("#F7F7F4")
    bars = ax.barh(labels, values, color=colors, height=0.68)

    ax.set_xlim(0, 1.08)
    ax.set_xlabel("Puntuación normalizada (0–1)", labelpad=12)
    ax.set_title(
        "Dashboard de confiabilidad actualizado",
        fontsize=23,
        loc="left",
        pad=32,
        color="#17313A",
    )
    ax.text(
        0,
        1.025,
        "GeoNormML + GeoNormPy · modelos espaciales oficiales",
        transform=ax.transAxes,
        fontsize=13,
        color="#52636A",
        va="bottom",
    )

    for bar, value in zip(bars, values):
        ax.text(
            value + 0.014,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.3f}",
            va="center",
            ha="left",
            fontsize=12.5,
            fontweight="bold",
            color="#26383E",
        )

    ax.xaxis.grid(True, color="#B8C3C6", alpha=0.42, linewidth=0.9)
    ax.yaxis.grid(False)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#8B999E")
    ax.tick_params(axis="y", length=0, pad=9)
    ax.tick_params(axis="x", colors="#52636A")

    fig.text(
        0.125,
        0.018,
        (
            "Fuentes: validación cruzada estratificada de 5 pliegues · "
            f"dataset v5 ({sample_count:,} muestras) · "
            f"GeoNormPy {tests_passed}/{tests_total} pruebas"
        ),
        fontsize=9.5,
        color="#65757B",
    )
    fig.subplots_adjust(left=0.29, right=0.95, top=0.82, bottom=0.15)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=300, facecolor=fig.get_facecolor())
    plt.close(fig)
    return OUTPUT_PATH


if __name__ == "__main__":
    output = create_dashboard()
    print(f"Dashboard generado: {output}")
