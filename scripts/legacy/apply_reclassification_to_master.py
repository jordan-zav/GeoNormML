from __future__ import annotations

import sys

import pandas as pd

from geonormml.config import DATASET_DIR, PROJECT_ROOT, setup_logging

logger = setup_logging("apply_reclassification_to_master")

INPUT_PATH = PROJECT_ROOT / "Dataset" / "Filtered" / "processed" / "Merge_Filtered_name_normalized.xlsx"
OUTPUT_DIR = DATASET_DIR
OUTPUT_PATH = OUTPUT_DIR / "Merge_Filtered_master_reclassified_v1.xlsx"
SUMMARY_PATH = OUTPUT_DIR / "Merge_Filtered_master_reclassified_v1_summary.txt"


MERGE_MAP = {
    "aplita": "granito",
    "mugearita": "traquiandesita basaltica",
    "dolerita": "gabro",
    "pitchstone": "riolita",
    "metatonalita": "tonalita",
    "adamelita": "monzogranito",
    "ortogranito": "granito",
    "metamonzogranito": "monzogranito",
    "basanita": "basalto",
    "monzogabro": "gabro",
    "basalto calcoalcalino": "basalto",
    "sienita": "monzonita",
    "traquibasalto": "basalto",
    "basalto alcalino": "basalto",
    "traquidacita": "riodacita",
    "traquita": "riodacita",
    "traquiandesita": "latita",
    "lamprofiro": "shoshonita",
}

EXCLUDE_CLASSES = {
    "lamproita",
    "gneis",
    "esquisto",
    "anfibolita",
    "arenisca tobacea",
    "toba",
    "toba cristalina",
    "toba litica",
    "toba vitrea",
    "tufo",
    "tufo de cristales",
    "porfido",
}


def main() -> None:
    if not INPUT_PATH.exists():
        logger.error("Input file not found: %s", INPUT_PATH)
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(INPUT_PATH, sheet_name="merge_normalized")
    original_rows = len(df)

    df["ROCK_NAME_BEFORE_RECLASS"] = df["ROCK_NAME"]
    df["ROCK_NAME"] = df["ROCK_NAME"].replace(MERGE_MAP)

    excluded_df = df[df["ROCK_NAME"].isin(EXCLUDE_CLASSES)].copy()
    final_df = df[~df["ROCK_NAME"].isin(EXCLUDE_CLASSES)].copy()

    changed_df = final_df[final_df["ROCK_NAME_BEFORE_RECLASS"] != final_df["ROCK_NAME"]].copy()

    final_counts = final_df["ROCK_NAME"].value_counts().rename_axis("ROCK_NAME").reset_index(name="count")
    excluded_counts = (
        excluded_df["ROCK_NAME_BEFORE_RECLASS"].value_counts().rename_axis("excluded_class").reset_index(name="count")
    )
    changed_counts = (
        changed_df[["ROCK_NAME_BEFORE_RECLASS", "ROCK_NAME"]]
        .value_counts()
        .reset_index(name="rows_changed")
        .sort_values(["rows_changed", "ROCK_NAME_BEFORE_RECLASS"], ascending=[False, True])
    )

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        final_df.to_excel(writer, sheet_name="master_reclassified", index=False)
        final_counts.to_excel(writer, sheet_name="class_frequency", index=False)
        excluded_counts.to_excel(writer, sheet_name="excluded_rows", index=False)
        changed_counts.to_excel(writer, sheet_name="applied_merges", index=False)

    summary_lines = [
        f"input_rows: {original_rows}",
        f"output_rows: {len(final_df)}",
        f"excluded_rows: {len(excluded_df)}",
        f"unique_classes_final: {final_df['ROCK_NAME'].nunique()}",
        "",
        "excluded_class_counts:",
        excluded_counts.to_string(index=False),
        "",
        "applied_merges:",
        changed_counts.to_string(index=False),
        "",
        "final_class_counts:",
        final_counts.to_string(index=False),
    ]
    SUMMARY_PATH.write_text("\n".join(summary_lines), encoding="utf-8")

    logger.info("Output: %s", OUTPUT_PATH)
    logger.info("Summary: %s", SUMMARY_PATH)
    logger.info("\n%s", "\n".join(summary_lines))


if __name__ == "__main__":
    main()
