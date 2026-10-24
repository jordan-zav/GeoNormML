"""Generate the compact dataset-cleaning graphic used by the GeoNorm totem."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, Wedge

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "artifacts" / "totem_geonorm"

PAPER_LIGHT = "#FAF8F2"
INK = "#17262D"
MUTED = "#5E6B70"
NAVY = "#102F3D"
TEAL = "#287C8E"
TEAL_LIGHT = "#DDECEF"
GREEN = "#4C956C"
COPPER = "#B66A4A"
LINE = "#D8D4CA"
WHITE = "#FFFFFF"

INITIAL = 3344
FINAL = 2755
RETAINED = FINAL / INITIAL
EXCLUDED = INITIAL - FINAL


def configure_arial() -> None:
    """Use Arial consistently in raster and vector exports."""
    arial = font_manager.findfont("Arial", fallback_to_default=False)
    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.sans-serif": [arial],
            "svg.fonttype": "none",
        }
    )


def rounded_box(ax, xy, width, height, facecolor, edgecolor="none", linewidth=0, radius=0.03):
    box = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=linewidth,
    )
    ax.add_patch(box)
    return box


def build_graphic() -> plt.Figure:
    fig = plt.figure(figsize=(4.7, 5.8), facecolor=PAPER_LIGHT)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    rounded_box(ax, (0.015, 0.015), 0.97, 0.97, WHITE, LINE, 1.4, 0.035)
    rounded_box(ax, (0.015, 0.855), 0.97, 0.13, NAVY, radius=0.035)
    ax.add_patch(plt.Rectangle((0.015, 0.855), 0.97, 0.065, color=NAVY, linewidth=0))

    ax.text(0.07, 0.925, "DEPURACIÓN", color=WHITE, fontsize=14, fontweight="bold", va="center")
    ax.text(0.07, 0.885, "Trazabilidad del QA/QC", color="#DDECEF", fontsize=9.5, va="center")

    center = (0.5, 0.635)
    radius = 0.175
    thickness = 0.052
    ax.add_patch(Wedge(center, radius, 90, 90 + 360, width=thickness, facecolor="#F1E2DA", edgecolor="none"))
    ax.add_patch(
        Wedge(
            center,
            radius,
            90,
            90 + 360 * RETAINED,
            width=thickness,
            facecolor=GREEN,
            edgecolor="none",
        )
    )
    ax.text(0.5, 0.66, "82,4 %", ha="center", va="center", color=NAVY, fontsize=24, fontweight="bold")
    ax.text(0.5, 0.605, "retenido", ha="center", va="center", color=MUTED, fontsize=10.5)

    rounded_box(ax, (0.075, 0.355), 0.35, 0.145, TEAL_LIGHT, radius=0.025)
    rounded_box(ax, (0.575, 0.355), 0.35, 0.145, "#E3EFE7", radius=0.025)
    ax.text(0.25, 0.443, "3 344", ha="center", va="center", color=TEAL, fontsize=21, fontweight="bold")
    ax.text(0.25, 0.39, "registros iniciales", ha="center", va="center", color=INK, fontsize=8.8)
    ax.text(0.75, 0.443, "2 755", ha="center", va="center", color=GREEN, fontsize=21, fontweight="bold")
    ax.text(0.75, 0.39, "muestras únicas", ha="center", va="center", color=INK, fontsize=8.8)

    ax.annotate(
        "",
        xy=(0.56, 0.427),
        xytext=(0.44, 0.427),
        arrowprops={"arrowstyle": "-|>", "color": NAVY, "lw": 1.8},
    )

    ax.plot([0.075, 0.925], [0.295, 0.295], color=LINE, linewidth=1)
    ax.text(0.5, 0.235, f"{EXCLUDED} registros excluidos", ha="center", color=COPPER, fontsize=12, fontweight="bold")
    ax.text(0.5, 0.185, "por criterios de depuración y QA/QC", ha="center", color=MUTED, fontsize=9.2)

    rounded_box(ax, (0.15, 0.075), 0.70, 0.065, PAPER_LIGHT, TEAL, 1.0, 0.018)
    ax.text(
        0.5,
        0.107,
        "IDs únicos después del control de calidad",
        ha="center",
        va="center",
        color=NAVY,
        fontsize=8.7,
        fontweight="bold",
    )

    return fig


def main() -> None:
    configure_arial()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig = build_graphic()
    fig.savefig(OUTPUT_DIR / "grafico_depuracion_dataset.png", dpi=400, facecolor=PAPER_LIGHT)
    fig.savefig(OUTPUT_DIR / "grafico_depuracion_dataset.svg", facecolor=PAPER_LIGHT)
    fig.savefig(OUTPUT_DIR / "grafico_depuracion_dataset.pdf", facecolor=PAPER_LIGHT)
    plt.close(fig)


if __name__ == "__main__":
    main()
