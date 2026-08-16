"""GeoNormML Pipeline Orchestrator.

Runs the full data-preparation → training → export pipeline, or any
subset of steps, in the canonical order.

Usage examples::

    # Run the complete pipeline
    python scripts/run_pipeline.py

    # Run only steps 6–8 (artifacts, benchmark, SHAP)
    python scripts/run_pipeline.py --from-step 6 --to-step 8

    # Run everything except spatial join
    python scripts/run_pipeline.py --skip-spatial

    # Show what would run without executing
    python scripts/run_pipeline.py --dry-run

    # List all steps
    python scripts/run_pipeline.py --list
"""

from __future__ import annotations

import argparse
import importlib
import sys
import time
from pathlib import Path

# Ensure the project root is on sys.path so "geonormml" is importable
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from geonormml.config import setup_logging  # noqa: E402

logger = setup_logging("run_pipeline")


# =====================================================================
# STEP REGISTRY  (order matters)
# =====================================================================

STEPS: list[dict[str, str]] = [
    {
        "num": 1,
        "name": "create_training_ready_dataset",
        "module": "scripts.create_training_ready_dataset",
        "desc": "Filter raw master -> training-ready v1",
        "spatial": False,
    },
    {
        "num": 2,
        "name": "assign_final_ids",
        "module": "scripts.assign_final_ids",
        "desc": "Assign deterministic ID_Final column",
        "spatial": False,
    },
    {
        "num": 3,
        "name": "apply_quality_filter",
        "module": "scripts.apply_quality_filter",
        "desc": "Apply geochemical quality flags (QF != 2)",
        "spatial": False,
    },
    {
        "num": 4,
        "name": "finalize_consistent_training_dataset",
        "module": "scripts.finalize_consistent_training_dataset",
        "desc": "Merge rare classes + produce v4 consistent",
        "spatial": False,
    },
    {
        "num": 5,
        "name": "spatial_join_dataset",
        "module": "scripts.spatial_join_dataset",
        "desc": "Enrich with geology 100k + fault distances",
        "spatial": True,
    },
    {
        "num": 6,
        "name": "build_modeling_artifacts",
        "module": "scripts.build_modeling_artifacts",
        "desc": "Generate splits, manifests, feature set catalog",
        "spatial": False,
    },
    {
        "num": 7,
        "name": "run_ml_benchmark",
        "module": "scripts.run_ml_benchmark",
        "desc": "Cross-validated benchmark (RF, SVM, XGB x feature sets)",
        "spatial": False,
    },
    {
        "num": 8,
        "name": "generate_shap_plots",
        "module": "scripts.generate_shap_plots",
        "desc": "SHAP interpretability plots",
        "spatial": False,
    },
    {
        "num": 9,
        "name": "export_official_models",
        "module": "scripts.export_official_models",
        "desc": "Export best models as .joblib bundles",
        "spatial": False,
    },
    {
        "num": 10,
        "name": "export_transfer_bundle_models",
        "module": "scripts.export_transfer_bundle_models",
        "desc": "Export full model catalog for PetroPyQAPF transfer",
        "spatial": False,
    },
    {
        "num": 11,
        "name": "generate_benchmark_figures",
        "module": "scripts.generate_benchmark_figures",
        "desc": "Generate Spanish benchmark metric figures",
        "spatial": False,
    },
    {
        "num": 12,
        "name": "generate_tas_comparison",
        "module": "scripts.generate_tas_comparison",
        "desc": "Generate TAS, CIPW and reported lithology comparison",
        "spatial": False,
    },
]


def print_step_list() -> None:
    """Display all available pipeline steps."""
    logger.info("Available pipeline steps:")
    logger.info("%-4s %-45s %s", "#", "Step Name", "Description")
    logger.info("-" * 80)
    for step in STEPS:
        tag = " [SPATIAL]" if step["spatial"] else ""
        logger.info(
            "%-4d %-45s %s%s",
            step["num"], step["name"], step["desc"], tag,
        )


def run_step(step: dict[str, str], dry_run: bool = False) -> bool:
    """Import and execute a single pipeline step. Returns True on success."""
    num = step["num"]
    name = step["name"]

    if dry_run:
        logger.info("  [DRY-RUN] Step %d: %s — %s", num, name, step["desc"])
        return True

    logger.info("=" * 70)
    logger.info("  Step %d/%d: %s", num, len(STEPS), name)
    logger.info("  %s", step["desc"])
    logger.info("=" * 70)

    t0 = time.perf_counter()
    try:
        mod = importlib.import_module(step["module"])
        mod.main()
        elapsed = time.perf_counter() - t0
        logger.info("  [OK]  %s completed in %.1fs", name, elapsed)
        return True
    except Exception:
        elapsed = time.perf_counter() - t0
        logger.exception("  [FAIL] %s failed after %.1fs", name, elapsed)
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="GeoNormML Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--from-step", type=int, default=1, metavar="N",
        help="Start from step N (default: 1)",
    )
    parser.add_argument(
        "--to-step", type=int, default=len(STEPS), metavar="N",
        help=f"End at step N (default: {len(STEPS)})",
    )
    parser.add_argument(
        "--skip-spatial", action="store_true",
        help="Skip spatial join step (step 5) even if in range",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show steps without executing them",
    )
    parser.add_argument(
        "--list", action="store_true", dest="list_steps",
        help="List all steps and exit",
    )
    args = parser.parse_args()

    if args.list_steps:
        print_step_list()
        return

    steps_to_run = [
        s for s in STEPS
        if args.from_step <= s["num"] <= args.to_step
    ]

    if args.skip_spatial:
        steps_to_run = [s for s in steps_to_run if not s["spatial"]]

    if not steps_to_run:
        logger.warning("No steps selected with --from-step %d --to-step %d", args.from_step, args.to_step)
        return

    mode = "DRY-RUN" if args.dry_run else "EXECUTE"
    logger.info("=" * 70)
    logger.info("  GeoNormML Pipeline — %s MODE", mode)
    logger.info("  Steps %d → %d (%d steps%s)",
                steps_to_run[0]["num"], steps_to_run[-1]["num"],
                len(steps_to_run),
                ", spatial skipped" if args.skip_spatial else "")
    logger.info("=" * 70)

    t_total = time.perf_counter()
    results: list[tuple[str, bool]] = []

    for step in steps_to_run:
        ok = run_step(step, dry_run=args.dry_run)
        results.append((step["name"], ok))
        if not ok and not args.dry_run:
            logger.error("Pipeline halted at step %d. Fix the error and re-run with --from-step %d",
                         step["num"], step["num"])
            break

    elapsed_total = time.perf_counter() - t_total

    # Summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("  PIPELINE SUMMARY  (%.1fs total)", elapsed_total)
    logger.info("=" * 70)
    for name, ok in results:
        status = "[OK]  " if ok else "[FAIL]"
        logger.info("  %s %s", status, name)

    n_fail = sum(1 for _, ok in results if not ok)
    if n_fail:
        logger.error("  %d step(s) failed.", n_fail)
        sys.exit(1)
    else:
        logger.info("  All %d steps completed successfully.", len(results))


if __name__ == "__main__":
    main()
