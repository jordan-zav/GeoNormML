"""Verify the public test suite from a newly extracted source distribution."""

import argparse
import os
import subprocess
import sys
import tarfile
from pathlib import Path, PurePosixPath


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--extract-to", type=Path, required=True)
    args = parser.parse_args()
    source, = args.directory.glob("geonormml-*.tar.gz")
    destination = args.extract_to.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    with tarfile.open(source) as archive:
        members = archive.getmembers()
        prefixes = set()
        for member in members:
            parts = PurePosixPath(member.name).parts
            target = destination.joinpath(*parts).resolve()
            if not parts or ".." in parts or not target.is_relative_to(destination):
                raise ValueError(f"Unsafe source member: {member.name}")
            if not (member.isfile() or member.isdir()):
                raise ValueError(f"Unexpected source member type: {member.name}")
            prefixes.add(parts[0])
        if len(prefixes) != 1:
            raise ValueError("Expected one source root")
        for member in members:
            target = destination.joinpath(*PurePosixPath(member.name).parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.extractfile(member).read())
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("GEONORMML_TEST_LOCAL_DATA", None)
    subprocess.run(
        [sys.executable, "-m", "pytest", "-q"], cwd=destination / prefixes.pop(), env=env, check=True,
    )


if __name__ == "__main__":
    main()
