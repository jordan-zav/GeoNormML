"""Exercise both real wheels outside their source trees, using installed scientific dependencies."""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ml-wheel", type=Path, required=True)
    parser.add_argument("--engine-wheel", type=Path, required=True)
    args = parser.parse_args()
    wheels = [str(p.resolve(strict=True)) for p in (args.ml_wheel, args.engine_wheel)]
    tests = Path(__file__).resolve().parents[1] / "tests/test_geonormpy_integration.py"
    code = """
import sys
sys.path[:0] = sys.argv[1:3]
import geonormml
import geonormpy
assert geonormml.__file__.startswith(sys.argv[1]), geonormml.__file__
assert geonormpy.__file__.startswith(sys.argv[2]), geonormpy.__file__
import pytest
raise SystemExit(pytest.main([
    sys.argv[3], '-q', '--import-mode=importlib', '-c', sys.argv[4],
]))
"""
    directory = Path(tempfile.mkdtemp(prefix="geonorm-pair-"))
    config = directory / "pytest.ini"
    config.write_text("[pytest]\n", encoding="utf-8")
    subprocess.run(
        [sys.executable, "-I", "-c", code, *wheels, str(tests), str(config)],
        cwd=directory, check=True,
    )
    print(f"Pair validation evidence retained in {directory}")


if __name__ == "__main__":
    main()
