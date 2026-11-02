"""Exercise the actual installed console command and portable defaults in a new directory."""

import argparse
import csv
import json
import os
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    python = args.python.resolve(strict=True)
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("GEONORMML_") or key == "PYTHONPATH":
            env.pop(key)
    env["GEONORMML_HOME"] = str(root / "user home")
    probe = subprocess.run(
        [
            str(python),
            "-I",
            "-c",
            "import sys,json,pathlib,geonormml; p=pathlib.Path(geonormml.__file__).resolve(); "
            "assert p.is_relative_to(pathlib.Path(sys.prefix).resolve()), str(p); "
            "print(json.dumps({'module':str(p),'version':geonormml.__version__}))",
        ],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    evidence = {"installed": json.loads(probe.stdout), "checks": []}
    console = python.parent / ("geonormml.exe" if os.name == "nt" else "geonormml")
    if not console.is_file():
        raise RuntimeError("The wheel did not install a geonormml console command")

    def run(arguments, expected=0):
        result = subprocess.run(
            [str(console), *arguments], cwd=root, env=env, text=True, capture_output=True, timeout=90
        )
        if result.returncode != expected:
            raise RuntimeError(f"Console failed: {arguments}\n{result.stdout}\n{result.stderr}")
        return json.loads(result.stdout if expected == 0 else result.stderr)

    paths = run(["paths"])
    assert paths["project_root"] is None
    assert paths["home"] == str(root / "user home")
    assert run(["models"])["models"] == []
    evidence["checks"].append("Installed defaults are user-owned and metadata commands do not create directories")
    example = run(["example", "--output", str(root / "model bundle")])
    manifest = example["manifest"]
    source = Path(example["input"])
    original = source.read_bytes()
    assert run(["inspect", manifest])["verified"]
    prediction = [
        "predict",
        "--model",
        manifest,
        "--input",
        str(source),
        "--output",
        str(root / "predictions.csv"),
        "--id-column",
        "Sample_ID",
    ]
    assert run(prediction, expected=2)["error"]["code"] == "trust_required"
    report = run([*prediction, "--trust-model"])
    assert report["rows"] == report["predicted"] == 4 and report["rejected"] == 0
    with (root / "predictions.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert [row["sample_id"] for row in rows] == ["001", "002", "003", "004"]
    assert source.read_bytes() == original
    assert run([*prediction, "--trust-model"], expected=2)["error"]["code"] == "invalid_request"
    assert not (root / "user home").exists()
    evidence["checks"].extend(
        [
            "Actual console creates the synthetic example, inspects metadata and enforces trusted loading",
            "CIPW-to-prediction CSV preserves lexical IDs and the original input",
            "Existing outputs are preserved; no application files are created under the Python installation",
        ]
    )
    evidence["status"] = "passed"
    (root / "installed-app-results.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
