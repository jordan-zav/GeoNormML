"""Genera figuras en español a partir del resumen de métricas del benchmark."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from geonormml.config import ARTIFACTS_DIR, ROCK_TYPE_COLUMN, TARGET_COLUMN, setup_logging  # noqa: E402
from geonormml.data import load_training_dataset  # noqa: E402

logger = setup_logging("generate_benchmark_figures")

SOURCE_PATH = ARTIFACTS_DIR / "ml_benchmark" / "metrics_summary.csv"
OUTPUT_DIR = ARTIFACTS_DIR / "ml_benchmark" / "figuras_resumen"

DOMAIN_LABELS = {"VOL": "Rocas volcánicas", "PLU": "Rocas plutónicas"}
MODEL_LABELS = {
    "RandomForest": "Random Forest",
    "SVM_PCA": "SVM + ACP",
    "XGBoost": "XGBoost",
}
METRICS = {
    "CA": "Exactitud (CA)",
    "AUC_macro_ovr": "AUC macro (OvR)",
    "F1_weighted": "F1 ponderado",
    "F1_macro": "F1 macro",
    "MCC": "Coeficiente de Matthews (MCC)",
}
OFFICIAL_MATRICES = {
    "VOL": "volcanic__combined_core__XGBoost.csv",
    "PLU": "plutonic__oxides_core__RandomForest.csv",
}


def save_figure(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_metric_heatmaps(data: pd.DataFrame, domain: str) -> None:
    """Compara todos los conjuntos de variables y modelos para métricas clave."""
    domain_data = data[data["domain"] == domain].copy()
    fig, axes = plt.subplots(1, len(METRICS), figsize=(24, 7), sharey=True)

    for ax, (column, label) in zip(axes, METRICS.items()):
        matrix = domain_data.pivot(index="feature_set", columns="modelo", values=column)
        matrix = matrix.reindex(columns=list(MODEL_LABELS.values()))
        sns.heatmap(
            matrix,
            ax=ax,
            cmap="YlGnBu",
            vmin=0,
            vmax=1,
            annot=True,
            fmt=".3f",
            linewidths=0.5,
            cbar=ax is axes[-1],
        )
        ax.set_title(label, fontweight="bold")
        ax.set_xlabel("Modelo")
        ax.tick_params(axis="x", rotation=45)
        if ax is axes[0]:
            ax.set_ylabel("Conjunto de variables")
        else:
            ax.set_ylabel("")

    fig.suptitle(f"Desempeño del benchmark — {DOMAIN_LABELS[domain]}", fontsize=16, fontweight="bold", y=1.03)
    save_figure(OUTPUT_DIR / f"mapa_metricas_{domain.lower()}.png")


def plot_model_comparison(data: pd.DataFrame, domain: str) -> None:
    """Resume el mejor resultado alcanzado por cada algoritmo en cada métrica."""
    best = data[data["domain"] == domain].groupby("modelo", as_index=False)[list(METRICS)].max()
    long = best.melt(id_vars="modelo", var_name="métrica", value_name="valor")
    long["métrica"] = long["métrica"].map(METRICS)

    plt.figure(figsize=(12, 6))
    sns.barplot(data=long, x="métrica", y="valor", hue="modelo", palette="colorblind")
    plt.ylim(0, 1.05)
    plt.xlabel("Métrica")
    plt.ylabel("Mejor valor de validación cruzada")
    plt.title(f"Mejor desempeño por algoritmo — {DOMAIN_LABELS[domain]}", fontweight="bold")
    plt.xticks(rotation=20, ha="right")
    plt.legend(title="Modelo")
    save_figure(OUTPUT_DIR / f"mejor_por_modelo_{domain.lower()}.png")


def plot_ranking(data: pd.DataFrame, domain: str, n: int = 10) -> pd.DataFrame:
    """Ordena configuraciones con un índice equilibrado de desempeño."""
    ranked = data[data["domain"] == domain].copy()
    ranked["índice_equilibrado"] = ranked[["CA", "AUC_macro_ovr", "F1_macro", "MCC"]].mean(axis=1)
    ranked = ranked.nlargest(n, "índice_equilibrado").sort_values("índice_equilibrado")
    ranked["configuración"] = ranked["modelo"] + " · " + ranked["feature_set"]

    plt.figure(figsize=(11, 6))
    bars = plt.barh(ranked["configuración"], ranked["índice_equilibrado"], color="#2c7fb8")
    plt.xlim(0, 1)
    plt.xlabel("Índice equilibrado (media de CA, AUC macro, F1 macro y MCC)")
    plt.ylabel("Configuración")
    plt.title(f"Diez configuraciones con mejor desempeño equilibrado — {DOMAIN_LABELS[domain]}", fontweight="bold")
    for bar, value in zip(bars, ranked["índice_equilibrado"]):
        plt.text(value + 0.01, bar.get_y() + bar.get_height() / 2, f"{value:.3f}", va="center")
    save_figure(OUTPUT_DIR / f"ranking_equilibrado_{domain.lower()}.png")
    return ranked


def plot_class_distribution(training_data: pd.DataFrame, domain: str) -> None:
    """Muestra el tamaño de cada clase y hace visible el desbalance del dataset."""
    counts = training_data[training_data[ROCK_TYPE_COLUMN] == domain][TARGET_COLUMN].value_counts().sort_values()
    plt.figure(figsize=(10, max(5, len(counts) * 0.55)))
    bars = plt.barh(counts.index, counts.values, color="#2c7fb8")
    plt.xlabel("Número de muestras")
    plt.ylabel("Clase litológica")
    plt.title(f"Frecuencia de clases litológicas — {DOMAIN_LABELS[domain]}", fontweight="bold")
    for bar, value in zip(bars, counts.values):
        plt.text(value + max(counts.values) * 0.01, bar.get_y() + bar.get_height() / 2, str(value), va="center")
    plt.xlim(0, max(counts.values) * 1.13)
    save_figure(OUTPUT_DIR / f"frecuencia_clases_{domain.lower()}.png")


def plot_class_performance(domain: str) -> None:
    """Calcula precisión, recall y F1 por clase desde la matriz oficial."""
    source = ARTIFACTS_DIR / "ml_benchmark" / "confusion_matrices" / OFFICIAL_MATRICES[domain]
    matrix = pd.read_csv(source, index_col=0)
    diagonal = pd.Series(matrix.values.diagonal(), index=matrix.index, dtype=float)
    precision = diagonal / matrix.sum(axis=0).replace(0, 1)
    recall = diagonal / matrix.sum(axis=1).replace(0, 1)
    f1 = 2 * precision * recall / (precision + recall).replace(0, 1)
    performance = pd.DataFrame({"Precisión": precision, "Recall": recall, "F1": f1}).sort_values("F1")

    ax = performance.plot.barh(figsize=(11, max(5, len(performance) * 0.55)), color=["#4daf4a", "#377eb8", "#e41a1c"])
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("Puntuación")
    ax.set_ylabel("Clase litológica")
    ax.set_title(f"Desempeño por clase del modelo de referencia — {DOMAIN_LABELS[domain]}", fontweight="bold")
    ax.legend(title="Métrica", loc="lower right")
    save_figure(OUTPUT_DIR / f"metricas_por_clase_{domain.lower()}.png")

    normalized = matrix.div(matrix.sum(axis=1), axis=0).fillna(0)
    plt.figure(figsize=(max(8, len(matrix) * 0.9), max(7, len(matrix) * 0.8)))
    sns.heatmap(normalized, cmap="YlOrRd", vmin=0, vmax=1, annot=True, fmt=".2f", square=True)
    plt.xlabel("Clase predicha")
    plt.ylabel("Clase real")
    plt.title(f"Matriz de confusión normalizada por clase real — {DOMAIN_LABELS[domain]}", fontweight="bold")
    save_figure(OUTPUT_DIR / f"matriz_normalizada_{domain.lower()}.png")


def main() -> None:
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(f"No se encontró el resumen de métricas: {SOURCE_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")
    data = pd.read_csv(SOURCE_PATH)
    data["modelo"] = data["model"].map(MODEL_LABELS).fillna(data["model"])
    training_data = load_training_dataset()

    rankings = []
    for domain in DOMAIN_LABELS:
        plot_metric_heatmaps(data, domain)
        plot_model_comparison(data, domain)
        rankings.append(plot_ranking(data, domain))
        plot_class_distribution(training_data, domain)
        plot_class_performance(domain)

    ranking = pd.concat(rankings, ignore_index=True)
    columns = ["domain", "modelo", "feature_set", "CA", "AUC_macro_ovr", "F1_macro", "MCC", "índice_equilibrado"]
    ranking[columns].to_csv(OUTPUT_DIR / "ranking_configuraciones.csv", index=False, encoding="utf-8-sig")
    logger.info("Figuras y ranking en español generados en %s", OUTPUT_DIR)


if __name__ == "__main__":
    main()
