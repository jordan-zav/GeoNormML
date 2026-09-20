"""Create an audited clean copy; never change the source workbook."""

import argparse
import json
from pathlib import Path

from geonormml.config import CLEAN_DATASET
from geonormml.quality import CURATED_POLICY, write_clean_dataset


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=CLEAN_DATASET)
    parser.add_argument("--sheet", default="training_ready_final")
    parser.add_argument(
        "--reference", type=Path, help="Verify every original value and ID against the curated workbook."
    )
    parser.add_argument("--policy", choices=(CURATED_POLICY, "restricted_experiment"), default=CURATED_POLICY)
    args = parser.parse_args()
    if args.policy == "restricted_experiment" and args.output.resolve() == CLEAN_DATASET.resolve():
        parser.error(
            "Restricted experiments require a separate --output; the default path is for the curated baseline."
        )
    print(
        json.dumps(
            write_clean_dataset(args.input, args.output, args.sheet, policy=args.policy, reference=args.reference),
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
