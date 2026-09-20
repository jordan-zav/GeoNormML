"""Create an audited clean copy; never change the source workbook."""

import argparse
import json
from pathlib import Path

from geonormml.config import CLEAN_DATASET
from geonormml.quality import write_clean_dataset


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=CLEAN_DATASET)
    parser.add_argument("--sheet", default="training_ready_final")
    args = parser.parse_args()
    print(json.dumps(write_clean_dataset(args.input, args.output, args.sheet), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
