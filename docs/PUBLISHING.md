# GeoNormML: PyPI candidate and publication procedure

Release version: 0.1.0. Preparing or pushing this repository does not publish a
package to PyPI. The explicit tagged publication workflow performs the upload;
verify its final result and the PyPI project before announcing availability.

## What is distributed

The wheel contains the reusable geonormml modules, installed CLI and package metadata. It
depends on released GeoNormPy 1.1.0. The source distribution adds research
scripts, synthetic tests, selected documentation and the existing public
publication-configuration fixtures needed by those tests.

Datasets, sample tables, trained weights, serialized estimators, credentials,
machine-specific configuration and application installers are excluded.
Research scripts are source-only tools; the wheel supplies no pretrained
classifier and no automatic research training or private-data download.

The [installed application guide](USAGE.md) covers portable paths, model
manifests, trusted loading, API/CLI inference and the synthetic example.
scripts/check_installed_app.py verifies the actual installed console command
in a fresh environment, including paths with spaces, lexical IDs and existing
output preservation. CI and candidate preparation both execute this check.

## Local candidate checks

Use the project's isolated Python 3.11 environment and local resource launcher.
Use a new distribution output directory for each candidate. On this PC archives
and logs belong under D:/DevResources/Sessions; extracted source code belongs
under O:/0. Projects. Preserve previous candidates.

    python -m pip check
    python -m ruff check src scripts tests
    python -m pytest -q
    python -m build --outdir PATH_TO_NEW_DIST
    python -m twine check --strict PATH_TO_NEW_DIST/geonormml-*
    python scripts/check_distribution.py PATH_TO_NEW_DIST
    python scripts/check_source_distribution.py PATH_TO_NEW_DIST --extract-to NEW_SOURCE_DIRECTORY

Download the released normative-engine wheel with pip download --no-deps
--only-binary=:all: geonormpy==1.1.0, then run:

    python scripts/check_installed_pair.py --ml-wheel PATH_TO_ML_WHEEL --engine-wheel PATH_TO_ENGINE_WHEEL

check_distribution.py writes SHA256SUMS.txt and verifies runtime/distribution/
citation versions, license, author, long description, dependency contract and
absence of private research files. The source extraction check runs the public
suite from the actual archive. Optional private-data tests stay disabled.

## Prepare on GitHub without publishing

Run Prepare or publish PyPI package (workflow pypi.yml) with publish=false.
It builds and checks both distributions, tests the extracted source and both
wheels, and uploads geonormml-distributions plus geonormml-checksums artifacts.
Its publication job is skipped. There is no release-created or push trigger.

## Configure publication when it is authorized

PyPI must have a pending Trusted Publisher for this new project, configured in
the owner's PyPI account with these exact values:

| Field | Value |
| --- | --- |
| PyPI project | geonormml |
| GitHub owner | jordan-zav |
| GitHub repository | GeoNormML |
| Workflow filename | pypi.yml |
| GitHub environment | pypi |

The repository alone cannot prove that this PyPI-side configuration is present.
Do not claim that publication is ready to authenticate until the owner configures
or verifies it. No PyPI token is stored in this repository; the publication job
uses a short-lived GitHub OIDC identity.

After explicit publication authorization, create the tag matching the package
version, for example v0.1.0, and run the workflow on that tag with publish=true.
The workflow rejects publication from a branch or a mismatched tag. The publish
job runs only after all candidate checks pass. Pushing commits or creating a
GitHub release alone never publishes this package.

After publication, verify the PyPI version, dependency metadata, license and
served SHA-256 hashes against the workflow artifacts. Test a normal installation
in a new environment. Published versions are immutable; use a new version for
later changes rather than replacing existing files.

Official references: [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/using-a-publisher/)
and [package metadata](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/).
