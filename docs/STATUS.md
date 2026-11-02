# GeoNormML: current state and remaining work

[Español](STATUS.es.md) · [Documentation index](README.md)

Updated 2 November 2026. This page separates operational adoption, historical
research and software integration. It does not supersede frozen experiment plans.

## Operational adoption

PetroPyQAPF adopted the frozen v5 final selector outputs on 27 October:

| Domain | Final configuration | Features | Eligible observations |
| --- | --- | --- | --- |
| VOL | HistGradientBoosting balanced15 | 12 oxide/auxiliary variables | 1,725 |
| PLU | RandomForest reference_leaf3 | 41 oxide, normative and contextual variables | 976 |

PLU requires GeoNormPy 1.1.0, Verma2003 profile 1.0, fixed ferric fraction 0.15,
carbonate_mode calcite and Ap + FAp. The source retains all 2,755 curated IDs;
54 observations outside the common eligible population remain in coverage records.

The internal selector mean macro F1 values, 0.635 / 0.389, evaluate the selection
procedure, not external performance of the final fitted weights. The operational
choice is explicit and exploratory. It does not establish superiority over every
alternative, geographic transfer or externally calibrated probabilities.
See the [adoption decision](revisiones/adopcion_petropyqapf_v5_20261027.md).

## Software integration

The installed CLI and Python API now cover portable paths, JSON model manifests,
SHA-256/environment checks, trusted loading, declared prepared-feature or chemical
input, per-row rejection and CSV output. A fully synthetic example is generated
on request outside the package. See the [application guide](USAGE.md).

Release 0.1.0 is prepared and verified separately from publication. Its wheel and
source archive include public code and regression resources, with checks against
private research files. The manual pypi.yml workflow prepares artifacts by default;
publication requires an explicit matching tag and publish=true. PyPI Trusted
Publisher configuration must be verified in the owner's account before upload.
See the [publication procedure](PUBLISHING.md).

- GeoNormML declares geonormpy==1.1.0 in package metadata and constraints.
- requirements.txt installs the released dependency without requiring a sibling
  checkout. requirements-local.txt provides paired editable development.
- The integration tests execute all three CIPW profiles, prepare profile-specific
  features, preprocess missing values and serialize a synthetic prediction fixture.
- The engine runtime version must agree with installed distribution metadata.
  An old editable-install metadata directory is not accepted as the new version.
- CI installs the exact released engine and runs the complete synthetic suite.
  No source dataset, fitted research model or private credentials are required.
- scripts/check_installed_pair.py verifies both built wheels from a fresh working
  directory in an isolated Python process. CI exercises the downloaded PyPI engine
  wheel together with the built GeoNormML wheel.

The tiny DummyClassifier fixture checks software plumbing only. It measures no
rock-classification accuracy. Research weights and the curated source are not
modified by these checks.

## Historical compatibility

CURRENT_GENERATION and the historical exporters retain curated_grouped_v2.
generation_catalog() preserves the publication snapshot; request
generation_catalog(include_operational=True) for the additional v5 adoption
metadata. A caller must not relabel a v2 artifact as v5 or replace its normative
features using the newer default engine. Reproduce historical environments from
their recorded versions and contracts.

The congress work is Legacy. v3/v4 comparisons and v5 stability diagnostics were
executed and remain dated evidence. Their inspected historical holdout is not a
new blind evaluation. Frozen figures and publication snapshots remain unchanged.

## Remaining scientific work

1. Acquire independent, provenance-checked chemistry and petrographic labels that
   were not inspected during selection or used in any final fit.
2. Freeze an external evaluation protocol before viewing its model outcomes.
3. Evaluate class coverage, confusion, macro F1, MCC and domain limitations;
   separate geographic claims from grouped internal validation.
4. Assess calibration and any rejection/abstention policy on separate development
   data before reporting final external performance.
5. Investigate plutonic class errors before proposing another model generation.

The [external evaluation plan](EXTERNAL_VALIDATION.md) records prerequisites and
the separation from research tuning. No external result is claimed here.
