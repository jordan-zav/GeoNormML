from __future__ import annotations

import pandas as pd

from geonormml.config import PROJECT_ROOT, setup_logging

logger = setup_logging("create_training_ready_dataset")

INPUT_PATH = PROJECT_ROOT / "Dataset" / "Filtered" / "final" / "Merge_Filtered_master_reclassified_v2_cipw.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "Dataset" / "Filtered" / "final"
OUTPUT_PATH = OUTPUT_DIR / "Merge_Filtered_training_ready_v1.xlsx"
SUMMARY_PATH = OUTPUT_DIR / "Merge_Filtered_training_ready_v1_summary.txt"
AUDIT_PATH = OUTPUT_DIR / "missing_core_oxides_audit.csv"


CORE_COLUMNS = ["SiO2", "Al2O3", "FeOT", "MgO", "CaO", "Na2O", "K2O"]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(INPUT_PATH, sheet_name="master_cipw")
    input_rows = len(df)

    missing_mask = df["Core_Oxides_Missing_Count"] > 0
    audit_df = df.loc[
        missing_mask,
        [
            "ID",
            "LAB_ID",
            "Source",
            "ROCK TYPE",
            "ROCK_NAME",
            "Core_Oxides_Missing_Count",
            *CORE_COLUMNS,
            "TiO2",
            "MnO",
            "P2O5",
            "LOI",
            "calc_error",
        ],
    ].copy()
    audit_df.to_csv(AUDIT_PATH, index=False, encoding="utf-8-sig")

    training_df = df.loc[~missing_mask].copy()

    class_frequency = training_df["ROCK_NAME"].value_counts().rename_axis("ROCK_NAME").reset_index(name="count")
    missing_by_class = audit_df["ROCK_NAME"].value_counts().rename_axis("ROCK_NAME").reset_index(name="rows_removed")
    missing_by_source = (
        audit_df["Source"].value_counts(dropna=False).rename_axis("Source").reset_index(name="rows_removed")
    )

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        training_df.to_excel(writer, sheet_name="training_ready", index=False)
        class_frequency.to_excel(writer, sheet_name="class_frequency", index=False)
        missing_by_class.to_excel(writer, sheet_name="removed_by_class", index=False)
        missing_by_source.to_excel(writer, sheet_name="removed_by_source", index=False)
        audit_df.to_excel(writer, sheet_name="removed_rows", index=False)

    summary_lines = [
        f"input_rows: {input_rows}",
        f"rows_removed_missing_core_oxides: {len(audit_df)}",
        f"output_rows_training_ready: {len(training_df)}",
        "",
        "removed_by_class:",
        missing_by_class.to_string(index=False),
        "",
        "removed_by_source:",
        missing_by_source.to_string(index=False),
        "",
        "final_class_counts:",
        class_frequency.to_string(index=False),
    ]
    SUMMARY_PATH.write_text("\n".join(summary_lines), encoding="utf-8")

    logger.info("Output:  %s", OUTPUT_PATH)
    logger.info("Summary: %s", SUMMARY_PATH)
    logger.info("Audit:   %s", AUDIT_PATH)
    logger.info("\n%s", "\n".join(summary_lines))


if __name__ == "__main__":
    main()
