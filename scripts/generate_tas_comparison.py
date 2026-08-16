"""Genera evidencia TAS para contrastar química, CIPW y litología reportada.

TAS se usa para las muestras volcánicas. En plutónicas se presenta únicamente
como espacio composicional: no sustituye la clasificación modal QAPF.
"""

from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.path import Path as MplPath

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from geonormml.config import ARTIFACTS_DIR, ROCK_TYPE_COLUMN, TARGET_COLUMN, setup_logging
from geonormml.data import load_training_dataset


logger = setup_logging("generate_tas_comparison")
OUTPUT_DIR = ARTIFACTS_DIR / "tas_comparison"
ANHYDROUS_OXIDES = ["SiO2", "TiO2", "Al2O3", "FeOT", "CaO", "MgO", "MnO", "Na2O", "K2O", "P2O5"]
DOMAIN_LABELS = {"VOL": "Rocas volcánicas", "PLU": "Rocas plutónicas"}

# Campos TAS que pueden compararse de forma directa con las categorías volcánicas
# presentes en ROCK_NAME. Las coordenadas corresponden a Le Bas et al. (1986).
TAS_POLYGONS = {
    "picrobasalto": [(35, 0), (45, 0), (45, 3), (41, 3), (41, 0)],
    "basalto": [(45, 0), (52, 0), (52, 5), (45, 5)],
    "andesita basaltica": [(52, 0), (57, 0), (57, 5.9), (52, 5)],
    "andesita": [(57, 0), (63, 0), (63, 7), (57, 5.9)],
    "dacita": [(63, 0), (69, 0), (69, 8), (63, 7)],
    "riolita": [(69, 0), (82, 0), (82, 8), (69, 8)],
    "traquibasalto": [(45, 5), (52, 5), (49.4, 7.3), (45, 9.4)],
    "traquiandesita basaltica": [(52, 5), (57, 5.9), (53, 9.3), (49.4, 7.3)],
    "traquiandesita": [(57, 5.9), (63, 7), (57.6, 11.7), (53, 9.3)],
}
TAS_COMPATIBILITY = {
    "picrobasalto": {"basalto"},
    "basalto": {"basalto"},
    "andesita basaltica": {"andesita basaltica"},
    "andesita": {"andesita"},
    "dacita": {"dacita", "riodacita"},
    "riolita": {"riolita"},
    "traquibasalto": {"basalto"},
    "traquiandesita basaltica": {"shoshonita"},
    "traquiandesita": {"benmoreita", "latita"},
}


def tas_coordinates(data: pd.DataFrame) -> pd.DataFrame:
    """Obtiene SiO2 y Na2O+K2O normalizados a 100 % anhidro."""
    result = data.copy()
    total = result[ANHYDROUS_OXIDES].sum(axis=1, min_count=len(ANHYDROUS_OXIDES))
    result["SiO2_TAS"] = 100 * result["SiO2"] / total
    result["Alcalis_TAS"] = 100 * (result["Na2O"] + result["K2O"]) / total
    return result.dropna(subset=["SiO2_TAS", "Alcalis_TAS"])


def assign_tas_field(data: pd.DataFrame) -> pd.DataFrame:
    """Asigna campos TAS volcánicos comparables; conserva como no asignado el resto."""
    result = data.copy()
    points = result[["SiO2_TAS", "Alcalis_TAS"]].to_numpy()
    result["TAS_FIELD"] = "otros campos TAS o fuera de rango"
    for field, vertices in TAS_POLYGONS.items():
        mask = MplPath(vertices, closed=True).contains_points(points, radius=1e-9)
        result.loc[mask, "TAS_FIELD"] = field
    return result


def setup_tas_axis(ax: plt.Axes, title: str, compositional_only: bool = False) -> None:
    ax.set_xlim(35, 82)
    ax.set_ylim(0, 16)
    # ASCII avoids missing-glyph warnings on Windows installations using Arial.
    ax.set_xlabel("SiO2 anhidro (% en peso)")
    ax.set_ylabel("Na2O + K2O anhidro (% en peso)")
    suffix = " — referencia composicional, no clasificación modal" if compositional_only else ""
    ax.set_title(title + suffix, fontweight="bold", fontsize=11)
    ax.grid(alpha=0.25)
    # Límites IUGS del TAS (Le Bas et al., 1986). No se asignan nombres TAS
    # porque algunos campos requieren criterios adicionales (p. ej., CO2).
    boundaries = [
        [(41, 3), (45, 3), (45, 5), (52, 5), (57, 5.9), (63, 7), (69, 8)],
        [(41, 3), (41, 7), (45, 9.4), (48.4, 11.5), (52.5, 14)],
        [(45, 5), (49.4, 7.3), (53, 9.3), (57.6, 11.7)],
        [(49.4, 7.3), (52, 5)],
        [(53, 9.3), (57, 5.9)],
        [(57.6, 11.7), (63, 7)],
        [(52.5, 14), (57.6, 11.7)],
    ]
    for boundary in boundaries:
        x, y = zip(*boundary)
        ax.plot(x, y, color="0.35", linewidth=1.1, linestyle="--", zorder=1)
    ax.text(70, 7.5, "límites TAS", fontsize=8, color="0.35")


def plot_domain(data: pd.DataFrame, domain: str) -> None:
    domain_data = data[data[ROCK_TYPE_COLUMN] == domain]
    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharex=True, sharey=True)

    for name, subset in domain_data.groupby(TARGET_COLUMN):
        axes[0].scatter(subset["SiO2_TAS"], subset["Alcalis_TAS"], s=18, alpha=0.65, label=name)
    setup_tas_axis(axes[0], f"TAS por litología reportada — {DOMAIN_LABELS[domain]}", domain == "PLU")
    axes[0].legend(title="Litología reportada", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)

    palette = {"oversaturated": "#377eb8", "undersaturated": "#e41a1c"}
    for state, subset in domain_data.groupby("silica_saturation"):
        axes[1].scatter(
            subset["SiO2_TAS"], subset["Alcalis_TAS"], s=18, alpha=0.65,
            label={"oversaturated": "Sobresaturada", "undersaturated": "Subsaturada"}.get(state, state),
            color=palette.get(state, "#666666"),
        )
    setup_tas_axis(axes[1], f"TAS y saturación normativa CIPW — {DOMAIN_LABELS[domain]}", domain == "PLU")
    axes[1].legend(title="CIPW", loc="upper left")
    fig.suptitle("Comparación composicional TAS, CIPW y litología", fontweight="bold", fontsize=15)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / f"tas_cipw_litologia_{domain.lower()}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_concordance(data: pd.DataFrame, domain: str) -> None:
    domain_data = data[data[ROCK_TYPE_COLUMN] == domain]
    table = pd.crosstab(domain_data[TARGET_COLUMN], domain_data["silica_saturation"], normalize="index")
    table = table.reindex(columns=["oversaturated", "undersaturated"], fill_value=0)
    table.columns = ["CIPW: sobresaturada", "CIPW: subsaturada"]
    table.to_csv(OUTPUT_DIR / f"concordancia_litologia_cipw_{domain.lower()}.csv", encoding="utf-8-sig")

    plt.figure(figsize=(7, max(5, len(table) * 0.55)))
    sns.heatmap(table, annot=True, fmt=".2f", cmap="Blues", vmin=0, vmax=1, linewidths=0.5)
    plt.xlabel("Saturación en sílice derivada de CIPW")
    plt.ylabel("Litología reportada")
    plt.title(f"Concordancia entre litología reportada y saturación CIPW — {DOMAIN_LABELS[domain]}", fontweight="bold")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / f"concordancia_litologia_cipw_{domain.lower()}.png", dpi=300, bbox_inches="tight")
    plt.close()


def plot_volcanic_tas_concordance(data: pd.DataFrame) -> None:
    """Resume la relación entre campo TAS y litología volcánica reportada."""
    volcanic = assign_tas_field(data[data[ROCK_TYPE_COLUMN] == "VOL"])
    assigned = volcanic[volcanic["TAS_FIELD"].isin(TAS_POLYGONS)].copy()
    assigned["compatible"] = assigned.apply(
        lambda row: row[TARGET_COLUMN] in TAS_COMPATIBILITY[row["TAS_FIELD"]], axis=1
    )

    summary = assigned.groupby("TAS_FIELD", sort=False).agg(
        n=(TARGET_COLUMN, "size"),
        litologias_compatibles=("TAS_FIELD", lambda values: ", ".join(sorted(TAS_COMPATIBILITY[values.iloc[0]]))),
        n_compatible=("compatible", "sum"),
        proporcion_compatible=("compatible", "mean"),
    )
    summary.to_csv(OUTPUT_DIR / "resumen_concordancia_tas_litologia_vol.csv", encoding="utf-8-sig")

    table = pd.crosstab(assigned["TAS_FIELD"], assigned[TARGET_COLUMN], normalize="index")
    table.to_csv(OUTPUT_DIR / "concordancia_tas_litologia_vol.csv", encoding="utf-8-sig")
    plt.figure(figsize=(11, max(5, len(table) * 0.7)))
    sns.heatmap(table, annot=True, fmt=".2f", cmap="Blues", vmin=0, vmax=1, linewidths=0.5)
    plt.xlabel("Litología reportada (ROCK_NAME)")
    plt.ylabel("Campo TAS asignado")
    plt.title("Concordancia TAS y litología reportada — rocas volcánicas", fontweight="bold")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "concordancia_tas_litologia_vol.png", dpi=300, bbox_inches="tight")
    plt.close()

    coverage = len(assigned) / len(volcanic) if len(volcanic) else 0
    logger.info("Concordancia TAS-volcánicas: %d/%d muestras en campos comparables (%.1f%%)", len(assigned), len(volcanic), 100 * coverage)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")
    data = tas_coordinates(load_training_dataset())
    for domain in DOMAIN_LABELS:
        plot_domain(data, domain)
        plot_concordance(data, domain)
    plot_volcanic_tas_concordance(data)

    (OUTPUT_DIR / "README.md").write_text(
        "# Componente TAS\n\n"
        "Las coordenadas se normalizan a 100 % anhidro con los óxidos mayores disponibles. "
        "TAS se usa como clasificación química de referencia en volcánicas; en plutónicas "
        "solo se muestra como espacio composicional y no reemplaza una clasificación modal QAPF. "
        "La columna ROCK_NAME representa la litología reportada del dataset, no una medición modal nueva.\n\n"
        "La matriz `concordancia_tas_litologia_vol.*` incluye únicamente los campos TAS volcánicos "
        "comparables con las categorías presentes en ROCK_NAME. Los demás campos TAS se conservan "
        "como no asignados para no forzar equivalencias petrológicas.\n\n"
        "Referencia: Le Bas, M. J., Le Maitre, R. W., Streckeisen, A. y Zanettin, B. (1986). "
        "A chemical classification of volcanic rocks based on the total alkali-silica diagram. "
        "Journal of Petrology, 27(3), 745–750. https://doi.org/10.1093/petrology/27.3.745\n",
        encoding="utf-8",
    )
    logger.info("Componente TAS generado en %s", OUTPUT_DIR)


if __name__ == "__main__":
    main()
