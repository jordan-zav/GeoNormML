from __future__ import annotations

import pandas as pd

from geonormml.config import DATASET_DIR, setup_logging

logger = setup_logging("apply_quality_filter")

INPUT_PATH = DATASET_DIR / "Merge_Filtered_training_ready_v2_with_final_id.xlsx"
OUTPUT_DIR = DATASET_DIR
OUTPUT_PATH = OUTPUT_DIR / "Merge_Filtered_training_ready_v3_quality_filtered.xlsx"
SUMMARY_PATH = OUTPUT_DIR / "Merge_Filtered_training_ready_v3_quality_filtered_summary.txt"


def recompute_quality_flag(df: pd.DataFrame) -> pd.Series:
    alk = df["Na2O"].fillna(0) + df["K2O"].fillna(0)
    SiO2 = df["SiO2"]
    LOI = df["LOI"]
    Sum_Oxs = df["Sum_Oxs"]
    Q = df["Q"]
    Ne = df["Ne"]
    Le = df["Le"]
    P2O5 = df["P2O5"]

    flag = pd.Series(0, index=df.index)
    flag[
        (LOI > 5)
        | (SiO2 > 82)
        | (alk < 0.5)
        | (Sum_Oxs < 90)
        | (Sum_Oxs > 110)
        | ((Q > 0) & ((Ne > 0) | (Le > 0)))
        | (Q > 90)
    ] = 2

    flag[
        (flag == 0)
        & (
            ((SiO2 >= 70) & (Q < 10))
            | ((SiO2 < 45) & (Q > 0))
            | ((SiO2 >= 52) & (SiO2 <= 63) & (Q > 30))
            | (P2O5 > 2)
            | ((alk >= 0.5) & (alk < 1))
            | ((SiO2 > 78) & (SiO2 <= 82))
        )
    ] = 1
    return flag


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")

    df = pd.read_excel(INPUT_PATH, sheet_name="training_ready")
    input_rows = len(df)

    df = df.copy()
    df["Quality_Flag_Recomputed"] = recompute_quality_flag(df)

    removed_df = df[df["Quality_Flag_Recomputed"] == 2].copy()
    kept_df = df[df["Quality_Flag_Recomputed"] != 2].copy()

    final_class_frequency = kept_df["ROCK_NAME"].value_counts().rename_axis("ROCK_NAME").reset_index(name="count")
    removed_by_class = removed_df["ROCK_NAME"].value_counts().rename_axis("ROCK_NAME").reset_index(name="rows_removed")
    flag_counts = (
        df["Quality_Flag_Recomputed"]
        .value_counts()
        .sort_index()
        .rename_axis("Quality_Flag_Recomputed")
        .reset_index(name="count")
    )

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        kept_df.to_excel(writer, sheet_name="training_ready_quality", index=False)
        final_class_frequency.to_excel(writer, sheet_name="class_frequency", index=False)
        removed_by_class.to_excel(writer, sheet_name="removed_flag2_by_class", index=False)
        flag_counts.to_excel(writer, sheet_name="quality_flag_counts", index=False)
        removed_df.to_excel(writer, sheet_name="removed_rows_flag2", index=False)

    summary_lines = [
        f"input_rows: {input_rows}",
        f"rows_removed_flag2: {len(removed_df)}",
        f"rows_kept: {len(kept_df)}",
        "",
        "quality_flag_counts:",
        flag_counts.to_string(index=False),
        "",
        "removed_by_class:",
        removed_by_class.to_string(index=False),
        "",
        "final_class_counts:",
        final_class_frequency.to_string(index=False),
        "",
        f"classes_below_20_after_filter: {int((final_class_frequency['count'] < 20).sum())}",
    ]
    SUMMARY_PATH.write_text("\n".join(summary_lines), encoding="utf-8")

    logger.info("Output written to %s", OUTPUT_PATH)
    logger.info("Summary written to %s", SUMMARY_PATH)
    logger.info("\n%s", "\n".join(summary_lines))


if __name__ == "__main__":
    main()
