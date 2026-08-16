from __future__ import annotations

from pathlib import Path

import pandas as pd
from geonormpy.norms.batch import calculate_cipw_dataframe


from geonormml.config import PROJECT_ROOT

INPUT_PATH = PROJECT_ROOT / "Dataset" / "Filtered" / "final" / "Merge_Filtered_master_reclassified_v1.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "Dataset" / "Filtered" / "final"
OUTPUT_PATH = OUTPUT_DIR / "Merge_Filtered_master_reclassified_v2_cipw.xlsx"
SUMMARY_PATH = OUTPUT_DIR / "Merge_Filtered_master_reclassified_v2_cipw_summary.txt"


VOLCANIC_CLASSES = {
    "andesita",
    "andesita basaltica",
    "basalto",
    "benmoreita",
    "dacita",
    "latita",
    "riodacita",
    "riolita",
    "shoshonita",
    "traquiandesita basaltica",
}

PLUTONIC_CLASSES = {
    "diorita",
    "gabro",
    "gabrodiorita",
    "granito",
    "granodiorita",
    "monzodiorita",
    "monzogranito",
    "monzonita",
    "sienogranito",
    "tonalita",
}

OXIDE_COLUMNS = [
    "SiO2",
    "TiO2",
    "Al2O3",
    "FeOT",
    "MnO",
    "MgO",
    "CaO",
    "Na2O",
    "K2O",
    "P2O5",
    "CO2",
    "S",
    "F",
    "Cl",
    "SO3",
]

CORE_COLUMNS = ["SiO2", "Al2O3", "FeOT", "MgO", "CaO", "Na2O", "K2O"]


def corrected_rock_type(rock_name: str) -> str:
    if rock_name in VOLCANIC_CLASSES:
        return "VOL"
    if rock_name in PLUTONIC_CLASSES:
        return "PLU"
    raise ValueError(f"Unmapped rock class for type correction: {rock_name}")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(INPUT_PATH, sheet_name="master_reclassified")

    df["ROCK_TYPE_BEFORE_CORRECTION"] = df["ROCK TYPE"]
    df["ROCK TYPE"] = df["ROCK_NAME"].map(corrected_rock_type)

    before = df["ROCK_TYPE_BEFORE_CORRECTION"].fillna("<<NULL>>")
    after = df["ROCK TYPE"]
    df["ROCK_TYPE_CORRECTION_FLAG"] = "unchanged"
    df.loc[df["ROCK_TYPE_BEFORE_CORRECTION"].isna(), "ROCK_TYPE_CORRECTION_FLAG"] = "filled_from_rock_name"
    df.loc[
        df["ROCK_TYPE_BEFORE_CORRECTION"].notna()
        & (df["ROCK_TYPE_BEFORE_CORRECTION"] != df["ROCK TYPE"]),
        "ROCK_TYPE_CORRECTION_FLAG",
    ] = "corrected_from_rock_name"

    df["Sum_Oxs"] = df[OXIDE_COLUMNS].fillna(0).sum(axis=1)
    df["Core_Oxides_Missing_Count"] = df[CORE_COLUMNS].isna().sum(axis=1)

    cipw_input = df[OXIDE_COLUMNS].copy()
    cipw_df = calculate_cipw_dataframe(cipw_input, fe3_fraction=0.15, strict=False)

    final_df = pd.concat([df.reset_index(drop=True), cipw_df.reset_index(drop=True)], axis=1)

    rock_type_audit = (
        pd.crosstab(
            final_df["ROCK_NAME"],
            final_df["ROCK TYPE"],
            dropna=False,
        )
        .reset_index()
    )
    flag_counts = (
        final_df["ROCK_TYPE_CORRECTION_FLAG"]
        .value_counts()
        .rename_axis("flag")
        .reset_index(name="count")
    )
    cipw_error_rows = final_df[final_df["calc_error"].notna()].copy()
    class_frequency = (
        final_df["ROCK_NAME"]
        .value_counts()
        .rename_axis("ROCK_NAME")
        .reset_index(name="count")
    )

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        final_df.to_excel(writer, sheet_name="master_cipw", index=False)
        class_frequency.to_excel(writer, sheet_name="class_frequency", index=False)
        rock_type_audit.to_excel(writer, sheet_name="rock_type_audit", index=False)
        flag_counts.to_excel(writer, sheet_name="rock_type_flags", index=False)
        cipw_error_rows.to_excel(writer, sheet_name="cipw_errors", index=False)

    summary_lines = [
        f"rows_total: {len(final_df)}",
        f"rock_type_filled_or_corrected: {int((final_df['ROCK_TYPE_CORRECTION_FLAG'] != 'unchanged').sum())}",
        "",
        "rock_type_flag_counts:",
        flag_counts.to_string(index=False),
        "",
        "rock_type_distribution:",
        final_df["ROCK TYPE"].value_counts(dropna=False).to_string(),
        "",
        f"rows_with_missing_core_oxides: {int((final_df['Core_Oxides_Missing_Count'] > 0).sum())}",
        f"cipw_error_rows: {len(cipw_error_rows)}",
        "",
        "final_class_counts:",
        class_frequency.to_string(index=False),
    ]
    SUMMARY_PATH.write_text("\n".join(summary_lines), encoding="utf-8")

    print(OUTPUT_PATH)
    print(SUMMARY_PATH)
    print("\n".join(summary_lines))


if __name__ == "__main__":
    main()
