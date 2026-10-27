"""Create or check the candidate-only adapter schema without copying model weights."""

import argparse
import json
from pathlib import Path

from geonormml.generation import dump_json, sha256


def transfer_schema(root):
    root = Path(root)
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    plan = json.loads((root / "frozen_plan.json").read_text(encoding="utf-8"))
    if not summary.get("complete") or not summary.get("originals_unchanged"):
        raise ValueError("Training did not complete with preserved source inputs")
    if sha256(root / "frozen_plan.json") != summary["plan_sha256"]:
        raise ValueError("The frozen training plan changed")
    models = []
    for item in summary["models"]:
        path = (root / item["artifact_path"]).resolve()
        if not path.is_relative_to(root.resolve()) or sha256(path) != item["artifact_sha256"]:
            raise ValueError("Candidate model path or checksum does not match the completed run")
        models.append(
            {
                **item,
                "model_name": item["selected"]["model_name"],
                "feature_set": item["selected"]["feature_set"],
                "model_type": "geochemical_baseline",
                "required_columns": item["feature_columns"],
                "status": "experimental",
                "warning": (
                    "Candidato con validación anidada interna; sin evaluación externa nueva. "
                    "No sustituye automáticamente al baseline."
                ),
            }
        )
    if {m["domain_code"] for m in models} != {"VOL", "PLU"} or len(models) != 2:
        raise ValueError("A candidate transfer requires exactly one selected model per domain")
    return {
        "project": "GeoNormML",
        "target_application": "PetroPyQAPF",
        "generation_id": summary["generation_id"],
        "release_status": summary["release_status"],
        "official_models": models,
        "wire_format_note": (
            "official_models is the existing transport key; every entry remains experimental, not promoted."
        ),
        "provenance": {
            "dataset_sha256": plan["dataset_sha256"],
            "plan_sha256": summary["plan_sha256"],
            "dependencies": plan["dependencies"],
        },
        "population": {"original_rows": summary["all_rows"], "common_eligible_rows": summary["eligible_rows"]},
        "input_contract": {
            "required": list(plan["cipw"]["required_measured_majors"]),
            "optional_imputed": ["LOI", "Sum_Oxs"],
            "assay_total": (
                "Preserve reported Sum_Oxs. Missing Sum_Oxs is fold-median imputed; never recompute silently."
            ),
            "normative_inputs": plan["cipw"],
            "imputation": "Training-fold medians; final preprocessing refit only at final export.",
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    schema = transfer_schema(args.run)
    destination = args.run / "schemas/official_model_bundle.json"
    if args.check:
        if json.loads(destination.read_text(encoding="utf-8")) != schema:
            raise ValueError("Existing adapter schema does not reproduce from training evidence")
        print("Candidate schema and model checksums verified")
        return
    if destination.exists():
        raise FileExistsError("Preserve the existing transfer schema; use --check to verify it")
    destination.parent.mkdir(exist_ok=True)
    dump_json(destination, schema)
    print(destination)


if __name__ == "__main__":
    main()
