"""Check public release metadata, regression resources and absence of local research files."""

import argparse
import ast
import email
import hashlib
import json
import tarfile
import zipfile
from pathlib import Path, PurePosixPath


def check_names(names):
    forbidden = {"dataset", "artifacts", ".git", ".venv", "__pycache__"}
    forbidden_files = {"agents.md", "auth.json", ".pypirc"}
    for name in names:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"Unsafe distribution path: {name}")
        if forbidden.intersection(part.casefold() for part in path.parts):
            raise ValueError(f"Local-only directory in distribution: {name}")
        if path.name.casefold() in forbidden_files or path.name.startswith((".env", ".devresources")):
            raise ValueError(f"Local-only configuration in distribution: {name}")
        if path.suffix.casefold() in {".xlsx", ".csv", ".joblib", ".pkl", ".pickle", ".sqlite", ".db"}:
            raise ValueError(f"Research input or serialized artifact in distribution: {name}")


def check_metadata(metadata, version):
    if metadata["Name"] != "geonormml" or metadata["Version"] != version:
        raise ValueError("Distribution and runtime versions disagree")
    if metadata["License-Expression"] != "GPL-3.0-or-later":
        raise ValueError("Unexpected license")
    if "geonormpy==1.1.0" not in metadata.get_all("Requires-Dist", []):
        raise ValueError("The exact normative engine dependency is missing")
    if metadata["Description-Content-Type"] != "text/markdown" or not metadata.get_payload().strip():
        raise ValueError("Missing PyPI long description")
    if not metadata["Author-email"] or not metadata.get_all("Project-URL"):
        raise ValueError("Missing author or project links")


def check_distribution(directory):
    wheel, = directory.glob("geonormml-*.whl")
    source, = directory.glob("geonormml-*.tar.gz")
    with zipfile.ZipFile(wheel) as archive:
        if archive.testzip() is not None:
            raise ValueError("Corrupt wheel")
        check_names(archive.namelist())
        metadata_path, = [p for p in archive.namelist() if p.endswith(".dist-info/METADATA")]
        tree = ast.parse(archive.read("geonormml/_version.py").decode("utf-8"))
        version, = [ast.literal_eval(node.value) for node in tree.body
                    if isinstance(node, ast.Assign) and any(
                        isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets
                    )]
        check_metadata(email.message_from_bytes(archive.read(metadata_path)), version)
        for module in ("catalog", "data", "expanded", "ml", "quality", "split"):
            archive.getinfo(f"geonormml/{module}.py")
    with tarfile.open(source) as archive:
        check_names(archive.getnames())
        prefix = f"geonormml-{version}/"
        required = (
            "PKG-INFO", "pyproject.toml", "LICENSE", "CITATION.cff", "docs/PYPI_README.md",
            "docs/PUBLISHING.md", "constraints-py311.txt", "src/geonormml/_version.py",
            "scripts/check_distribution.py", "scripts/check_installed_pair.py",
            "scripts/check_source_distribution.py", "tests/test_geonormpy_integration.py",
            "poster_cpg23/configs/current_baseline.evidence.json",
        )
        for name in required:
            archive.getmember(prefix + name)
        check_metadata(email.message_from_bytes(archive.extractfile(prefix + "PKG-INFO").read()), version)
        citation = archive.extractfile(prefix + "CITATION.cff").read().decode("utf-8")
        if f'version: "{version}"' not in citation.splitlines():
            raise ValueError("Citation version disagrees with distribution")
    sums = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (wheel, source)}
    return {"version": version, "license": "GPL-3.0-or-later", "sha256": sums,
            "private_research_files_included": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    result = check_distribution(args.directory)
    (args.directory / "SHA256SUMS.txt").write_text(
        "".join(f"{digest}  {name}\n" for name, digest in sorted(result["sha256"].items())), encoding="ascii",
    )
    print(json.dumps(result, indent=2))
