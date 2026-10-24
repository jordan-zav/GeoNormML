from __future__ import annotations

from pathlib import Path

import matplotlib.patheffects as PathEffects
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import PowerNorm

from geonormml.config import PROJECT_ROOT, setup_logging

logger = setup_logging("generate_report_confusion_matrices")

ROOT = PROJECT_ROOT
SOURCE_DIR = ROOT / "artifacts" / "ml_benchmark" / "confusion_matrices"
OUTPUT_DIR = ROOT / "artifacts" / "report_confusion_matrices_2025_context"

MATRICES = [
    {
        "sheet": "VOL_RF",
        "source": "volcanic__combined_core__RandomForest.csv",
        "title": "Matriz de confusion - Volcanicas - Random Forest",
    },
    {
        "sheet": "VOL_XGB",
        "source": "volcanic__combined_core__XGBoost.csv",
        "title": "Matriz de confusion - Volcanicas - XGBoost",
    },
    {
        "sheet": "VOL_SVM_PCA",
        "source": "volcanic__combined_core__SVM_PCA.csv",
        "title": "Matriz de confusion - Volcanicas - SVM + PCA",
    },
    {
        "sheet": "PLU_RF",
        "source": "plutonic__oxides_core__RandomForest.csv",
        "title": "Matriz de confusion - Plutonicas - Random Forest",
    },
    {
        "sheet": "PLU_XGB",
        "source": "plutonic__oxides_core__XGBoost.csv",
        "title": "Matriz de confusion - Plutonicas - XGBoost",
    },
    {
        "sheet": "PLU_SVM_PCA",
        "source": "plutonic__oxides_core__SVM_PCA.csv",
        "title": "Matriz de confusion - Plutonicas - SVM + PCA",
    },
]


def read_matrix(source_name: str) -> pd.DataFrame:
    path = SOURCE_DIR / source_name
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path, index_col=0)


def plot_matrix(df: pd.DataFrame, title: str, out_path: Path) -> None:
    values = df.to_numpy()
    n_rows, n_cols = values.shape
    local_min = values.min()
    local_max = max(values.max(), 1)

    norm = PowerNorm(gamma=0.6, vmin=local_min, vmax=local_max)

    width = max(12, n_cols * 1.15)
    height = max(10, n_rows * 1.05)
    fig = plt.figure(figsize=(width, height))
    ax = fig.add_axes([0.10, 0.18, 0.74, 0.72])
    cax = fig.add_axes([0.87, 0.18, 0.03, 0.72])

    im = ax.imshow(values, cmap="plasma", norm=norm, interpolation="bilinear")

    ax.set_xticks(range(n_cols))
    ax.set_yticks(range(n_rows))
    ax.set_xticklabels(df.columns, rotation=90, fontsize=14)
    ax.set_yticklabels(df.index, fontsize=14)
    ax.set_xlabel("Predicha", fontsize=16, fontweight="bold", labelpad=16)
    ax.set_ylabel("Real", fontsize=16, fontweight="bold")
    ax.set_title(title, fontsize=18, fontweight="bold", pad=18)

    cbar = fig.colorbar(im, cax=cax)
    cbar.set_label("Numero de muestras", fontsize=14, fontweight="bold", labelpad=18)
    cbar.ax.tick_params(labelsize=12)

    for i in range(n_rows):
        for j in range(n_cols):
            label = str(int(values[i, j]))
            txt = ax.text(
                j,
                i,
                label,
                ha="center",
                va="center",
                color="white",
                fontsize=13,
                fontweight="bold",
            )
            txt.set_path_effects([PathEffects.withStroke(linewidth=2, foreground="black")])

    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    workbook_path = OUTPUT_DIR / "confusion_matrices_2025_context.xlsx"
    with pd.ExcelWriter(workbook_path) as writer:
        for item in MATRICES:
            df = read_matrix(item["source"])
            df.to_excel(writer, sheet_name=item["sheet"])
            plot_matrix(df, item["title"], OUTPUT_DIR / f"heatmap_{item['sheet']}.png")

    summary_lines = [
        "Matrices de confusion generadas para el contexto actual de GeoNormML.",
        "",
        "Criterio usado:",
        "Volcanicas: feature set combined_core, equivalente al modelo oficial recomendado.",
        "Plutonicas: feature set oxides_core, equivalente al modelo oficial recomendado.",
        "",
        "Archivos generados:",
        str(workbook_path),
    ]
    for item in MATRICES:
        summary_lines.append(str(OUTPUT_DIR / f"heatmap_{item['sheet']}.png"))

    (OUTPUT_DIR / "resumen.txt").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    logger.info("\n%s", "\n".join(summary_lines))


if __name__ == "__main__":
    main()
