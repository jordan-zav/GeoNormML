from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from geonormpy.norms.batch import calculate_cipw_dataframe

from geonormml.config import setup_logging

logger = setup_logging("run_cipw_from_csv")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compute CIPW normative minerals from a geochemical CSV.")
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the input CSV with major oxides.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to the output CSV with original data plus CIPW results.",
    )
    parser.add_argument(
        "--fe3-fraction",
        type=float,
        default=0.15,
        help="Default Fe3+ fraction used when only FeOT is available.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Raise stricter errors for iron inconsistencies.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)
    logger.info("Loaded %d rows from %s", len(df), input_path.name)

    cipw_df = calculate_cipw_dataframe(
        df,
        fe3_fraction=args.fe3_fraction,
        strict=args.strict,
    )

    combined_df = pd.concat([df.reset_index(drop=True), cipw_df.reset_index(drop=True)], axis=1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined_df.to_csv(output_path, index=False)

    logger.info("Processed %d rows", len(df))
    logger.info("Saved results to: %s", output_path)


if __name__ == "__main__":
    main()
