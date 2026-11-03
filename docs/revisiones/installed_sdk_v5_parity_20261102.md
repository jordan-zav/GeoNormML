# Installed SDK and frozen v5 models: parity audit

Date: 2026-11-02. Generation: partition_stability_v5_20261027.

GeoNormML 0.1.0 installed from PyPI was checked outside the source checkout
against the trusted private transfer. All 1,382 manifest entries passed their
recorded size and SHA-256 checks before model deserialization. The curated
source, frozen plan, population and normative tables matched their recorded
hashes. The source files were checked again after execution and were unchanged.

| Model | Eligible rows | Features | Labels | Maximum probability difference |
| --- | ---: | ---: | --- | ---: |
| VOL HistGradientBoosting | 1,725 | 12 | Identical | 0 |
| PLU RandomForest | 976 | 41 | Identical | 0 |

Both prepared-feature and raw-chemistry API routes passed. Feature differences
against the frozen reference were zero for VOL and at most 7.11e-15 for PLU.
Checks also covered absent optional LOI/total measurements and measured negative
LOI. No estimator was fitted, selected or replaced.

The historical artifacts lack the SDK's complete raw-input metadata. Separate
private adapters therefore wrap the same fitted estimators and record the frozen
feature order, class order, normative contract and source hashes. Original
weights remain intact. The adapter serialization environment is recorded
separately: the original training Python version is unknown. This audit verifies
parity in the current compatible environment, not reconstruction of an
unrecorded original interpreter.

The reusable audit entry point is scripts/audit_transferred_models.py. It requires
an explicitly trusted transfer, the matching curated workbook and a new private
output directory. Reports, predictions and adapters remain outside the public
repository. Joblib input must never be accepted from untrusted sources.

## Scientific limits

Saved internal OOF labels were checked against source labels and group/fold
assignments. Class reports and confusion matrices were reconstructed and checked
against recorded summaries. Repeated partitions describe the selection
procedure; they are correlated and are not independent replications or external
evaluation of final fitted weights.

No per-class OOF probabilities were saved. Brier score, log loss and probability
calibration cannot be reconstructed honestly from hard labels. Probabilities
from final models evaluated on their fitting rows do not resolve this gap.
External validation and independent calibration remain pending.

Prior-generation v4 weights were deliberately absent from the transfer. They
were recorded as unavailable ancestors; no v4 comparison or refit was attempted.
No research weights, samples or row-level reports were added to PyPI or GitHub.

## Resumen en español

La API instalada reproduce las etiquetas y probabilidades originales en las
2.701 filas elegibles de v5. Se verificaron hashes, variables, contratos y rutas
de entrada, sin reentrenar ni alterar originales. La revisión interna por clase
se conserva en informes privados. Esto cierra la comprobación de integración
con los pesos reales, pero no la validación externa ni la calibración: faltan
probabilidades OOF y datos independientes con etiquetas verificadas.
