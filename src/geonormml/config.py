from __future__ import annotations

import logging
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATASET_DIR = PROJECT_ROOT / "Dataset" / "Filtered" / "final"
SPATIAL_DATASET = DATASET_DIR / "Merge_Filtered_training_ready_v5_spatial.xlsx"
CONSISTENT_DATASET = DATASET_DIR / "Merge_Filtered_training_ready_v4_consistent.xlsx"
DATASET_PATH = SPATIAL_DATASET if SPATIAL_DATASET.exists() else CONSISTENT_DATASET
DATASET_SHEET = "training_ready_final"

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
SPLITS_DIR = ARTIFACTS_DIR / "splits"
MANIFESTS_DIR = ARTIFACTS_DIR / "manifests"

TARGET_COLUMN = "ROCK_NAME"
ROCK_TYPE_COLUMN = "ROCK TYPE"
ID_COLUMN = "ID_Final"

RANDOM_STATE = 42
TEST_SIZE = 0.2
CV_FOLDS = 5


def setup_logging(
    name: str = "geonormml",
    *,
    level: int = logging.INFO,
    log_file: Path | None = None,
) -> logging.Logger:
    """Configure and return a logger with consistent formatting.

    Parameters
    ----------
    name : str
        Logger name (typically the script basename).
    level : int
        Logging level (default INFO).
    log_file : Path | None
        If provided, also writes log output to this file.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    logger.setLevel(level)
    fmt = logging.Formatter(
        "[%(asctime)s %(levelname)-7s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Use UTF-8 stream to avoid cp1252 errors on Windows
    stream = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace", closefd=False)
    console = logging.StreamHandler(stream)
    console.setFormatter(fmt)
    logger.addHandler(console)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger
