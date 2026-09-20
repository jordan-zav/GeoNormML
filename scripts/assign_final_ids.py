from __future__ import annotations

import pandas as pd

from geonormml.config import DATASET_DIR, setup_logging

logger = setup_logging("assign_final_ids")

INPUT_PATH = DATASET_DIR / "Merge_Filtered_training_ready_v1.xlsx"
OUTPUT_DIR = DATASET_DIR
OUTPUT_PATH = OUTPUT_DIR / "Merge_Filtered_training_ready_v2_with_final_id.xlsx"
SUMMARY_PATH = OUTPUT_DIR / "Merge_Filtered_training_ready_v2_with_final_id_summary.txt"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")

    df = pd.read_excel(INPUT_PATH, sheet_name="training_ready")

    df = df.copy()
    df.insert(0, "ID_Final", range(1, len(df) + 1))

    class_frequency = df["ROCK_NAME"].value_counts().rename_axis("ROCK_NAME").reset_index(name="count")

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="training_ready", index=False)
        class_frequency.to_excel(writer, sheet_name="class_frequency", index=False)

    summary_lines = [
        f"rows_total: {len(df)}",
        f"id_final_min: {int(df['ID_Final'].min())}",
        f"id_final_max: {int(df['ID_Final'].max())}",
        f"id_final_unique: {int(df['ID_Final'].nunique())}",
        f"legacy_id_unique: {int(df['ID'].nunique())}",
        "",
        "first_10_id_pairs:",
        df[["ID_Final", "ID", "LAB_ID", "ROCK_NAME"]].head(10).to_string(index=False),
    ]
    SUMMARY_PATH.write_text("\n".join(summary_lines), encoding="utf-8")

    logger.info("Output written to %s", OUTPUT_PATH)
    logger.info("Summary written to %s", SUMMARY_PATH)
    logger.info("\n%s", "\n".join(summary_lines))


if __name__ == "__main__":
    main()
