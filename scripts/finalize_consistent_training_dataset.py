from __future__ import annotations

import pandas as pd

from geonormml.config import DATASET_DIR, setup_logging

logger = setup_logging("finalize_consistent_training_dataset")

INPUT_PATH = DATASET_DIR / "Merge_Filtered_training_ready_v3_quality_filtered.xlsx"
OUTPUT_DIR = DATASET_DIR
OUTPUT_PATH = OUTPUT_DIR / "Merge_Filtered_training_ready_v4_consistent.xlsx"
SUMMARY_PATH = OUTPUT_DIR / "Merge_Filtered_training_ready_v4_consistent_summary.txt"

FINAL_MERGES = {
    "traquiandesita basaltica": "shoshonita",
}

MIN_CLASS_SIZE = 20


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")

    df = pd.read_excel(INPUT_PATH, sheet_name="training_ready_quality")
    input_rows = len(df)

    df = df.copy()
    df["ROCK_NAME_BEFORE_FINAL_MERGE"] = df["ROCK_NAME"]
    df["ROCK_NAME"] = df["ROCK_NAME"].replace(FINAL_MERGES)

    final_class_frequency = df["ROCK_NAME"].value_counts().rename_axis("ROCK_NAME").reset_index(name="count")
    changed_rows = df[df["ROCK_NAME_BEFORE_FINAL_MERGE"] != df["ROCK_NAME"]].copy()
    changed_summary = (
        changed_rows[["ROCK_NAME_BEFORE_FINAL_MERGE", "ROCK_NAME"]].value_counts().reset_index(name="rows_changed")
    )

    classes_below_min = final_class_frequency[final_class_frequency["count"] < MIN_CLASS_SIZE]

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="training_ready_final", index=False)
        final_class_frequency.to_excel(writer, sheet_name="class_frequency", index=False)
        changed_summary.to_excel(writer, sheet_name="final_merges", index=False)
        classes_below_min.to_excel(writer, sheet_name="classes_below_20", index=False)

    summary_lines = [
        f"input_rows: {input_rows}",
        f"output_rows_final: {len(df)}",
        f"minimum_class_size_required: {MIN_CLASS_SIZE}",
        "",
        "final_merges:",
        changed_summary.to_string(index=False) if not changed_summary.empty else "None",
        "",
        "final_class_counts:",
        final_class_frequency.to_string(index=False),
        "",
        f"classes_below_20_after_final_merge: {len(classes_below_min)}",
    ]
    SUMMARY_PATH.write_text("\n".join(summary_lines), encoding="utf-8")

    logger.info("Output written to %s", OUTPUT_PATH)
    logger.info("Summary written to %s", SUMMARY_PATH)
    logger.info("\n%s", "\n".join(summary_lines))


if __name__ == "__main__":
    main()
