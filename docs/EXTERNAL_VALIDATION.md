# External evaluation preparation

Status: prerequisites and protocol outline; not an executed external evaluation.
This document does not alter the frozen v3/v4/v5 experimental plans.

## Eligible evidence

Use a separately sourced cohort with traceable major-oxide units, analytical
totals, iron reporting conventions and independently assigned petrographic
labels. Record source, license, collection date, laboratory identifiers,
coordinates where available and the class-mapping decision. Normative chemistry
or the classifier itself must not generate the reference labels being evaluated.

Before eligibility decisions, check sample identifiers, source publications,
replicates and chemical duplicates against all prior development and final-fit
observations. Record uncertain matches for adjudication. A geographic holdout
formed after inspecting previous outcomes is a diagnostic, not automatically a
new independent cohort.

## Freeze before inference

Record hashes of the input cohort, labels, eligible population, model binaries,
feature names/order, engine version, CIPW profile, iron/carbonate policies,
preprocessing and class mapping. Use separate new output directories. Keep all
excluded or unsupported rows in coverage records with explicit reasons.

The adopted PLU contract is Verma2003 1.0 in GeoNormPy 1.1.0, fixed ferric
fraction 0.15, calcite assumption, Ap + FAp and the recorded category strings.
Preserve missing LOI/analytical totals for the trained imputer; measured negative
LOI remains valid. Loading an artifact alone does not verify this input contract.

Specify primary metrics, eligible classes, dependency groups, uncertainty method,
missing-label handling and any scientific acceptance criteria before reading
external model outcomes. Acceptance thresholds are not invented retrospectively
in this software integration task.

## Execute and report

Run the frozen predictor once per predeclared analysis. Do not refit on the test
cohort. Report the full confusion matrix, class support, per-class recall,
accuracy, macro F1, MCC and coverage of rejected or unsupported observations.
Report uncertainty respecting known sample/source groups and disclose small or
absent classes. List classes absent from training separately.

Examine probabilistic calibration with appropriate reliability and scoring
diagnostics. If calibration or abstention rules are fitted, use a separate
development cohort or a predeclared nested design; retain untouched final data.
Selecting a calibration or rejection threshold on the final test is tuning.

Separate the descriptive results by domain and source. Claims about transfer to
another region require an appropriate independent geographic design. Do not
translate the internal selector macro F1 into a per-sample confidence value.

## Current boundary

No new independent cohort was acquired or certified during this integration.
Synthetic integration tests exercise software only. The historical inspected
holdout and the final-fit population cannot close this scientific pending item.
