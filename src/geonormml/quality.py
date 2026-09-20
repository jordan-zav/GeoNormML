"""Conservative dataset checks with row-level provenance and no inferred assays."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .features import CIPW_FEATURES, OXIDE_FEATURES_EXTENDED

CORE = ["SiO2", "Al2O3", "FeOT", "MgO", "CaO", "Na2O", "K2O"]
SPATIAL = ["UTM_Zone", "Geol_Unit", "Geol_Age_100k", "Geol_Lith_100k", "Metal_Belt", "Fault_Dist"]
CURATED_POLICY = "preserve_curated_v1"


def collapse_spatial_matches(frame: pd.DataFrame, attributes: list[str]) -> pd.DataFrame:
    """Keep one sample per ID; ambiguous map attributes become missing, not arbitrary labels."""
    if "ID_Final" not in frame or frame.ID_Final.isna().any():
        raise ValueError("Spatial data requires nonmissing ID_Final values.")
    attrs = [c for c in attributes if c in frame]
    other = [c for c in frame if c not in attrs and c != "ID_Final"]
    grouped = frame.groupby("ID_Final", sort=False, dropna=False)
    conflicts = grouped[other].nunique(dropna=False).gt(1)
    if conflicts.any().any():
        raise ValueError("Repeated ID_Final has conflicting sample data; spatial collapse is unsafe.")
    result = frame.drop_duplicates("ID_Final").copy().set_index("ID_Final", drop=False)
    for column in attrs:
        values = grouped[column].agg(lambda s: sorted(set(s.dropna()), key=str))
        ambiguous = values.map(len).gt(1)
        result[column] = values.map(lambda v: v[0] if len(v) == 1 else np.nan)
        # Preserve every candidate for human review, outside predictor feature sets.
        result[f"{column}_Candidates"] = values.map(lambda v: json.dumps(v, ensure_ascii=False))
        result[f"{column}_Ambiguous"] = ambiguous
    return result.reset_index(drop=True)


def sample_groups(df: pd.DataFrame) -> pd.Series:
    """Connected groups for repeated laboratory IDs or identical core chemistry.

    Conservative grouping prevents assay replicates from crossing validation folds.
    This is sample grouping, not a claim of spatially independent validation.
    """
    n = len(df)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union_keys(columns, require_complete=True):
        seen = {}
        for i, values in enumerate(df[columns].itertuples(index=False, name=None)):
            if require_complete and any(pd.isna(v) or str(v).strip() == "" for v in values):
                continue
            key = tuple(None if pd.isna(v) else v for v in values)
            if key in seen:
                left, right = find(i), find(seen[key])
                parent[max(left, right)] = min(left, right)
            else:
                seen[key] = i

    if {"Source", "LAB_ID"}.issubset(df):
        union_keys(["Source", "LAB_ID"])
    if set(CORE).issubset(df):
        union_keys(CORE)
    # Existing externally assigned groups are an additional constraint.
    if "Sample_Group" in df:
        union_keys(["Sample_Group"])
    ids = df["ID_Final"].astype(str).tolist() if "ID_Final" in df else [str(i) for i in range(n)]
    members = {}
    for i in range(n):
        members.setdefault(find(i), []).append(ids[i])
    names = {
        root: "sample-" + hashlib.sha256("|".join(sorted(values)).encode()).hexdigest()[:16]
        for root, values in members.items()
    }
    return pd.Series([names[find(i)] for i in range(n)], index=df.index, name="Sample_Group")


def clean_dataset(frame: pd.DataFrame, *, policy: str = CURATED_POLICY) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Preserve curated sample IDs; extra scientific/duplicate checks are warnings.

    The former restrictive policy is only available as an explicit experiment.
    """
    if policy not in {CURATED_POLICY, "restricted_experiment"}:
        raise ValueError(f"Unknown cleaning policy: {policy}")
    required = ["ID_Final", "Source", "LAB_ID", "ROCK TYPE", "ROCK_NAME", *CORE]
    missing = sorted(set(required) - set(frame))
    if missing:
        raise ValueError(f"Missing required dataset columns: {missing}")
    df = frame.copy()
    if df.columns.duplicated().any():
        raise ValueError("Duplicate column names are not allowed.")
    changes = {}
    for column in df.select_dtypes(include=["object", "string"]):
        before = df[column].copy()
        df[column] = df[column].map(lambda v: v.strip() if isinstance(v, str) else v).replace("", np.nan)
        count = int((before.fillna("") != df[column].fillna("")).sum())
        if count:
            changes[column] = count
    numeric = set(
        OXIDE_FEATURES_EXTENDED
        + CIPW_FEATURES
        + [
            "ID_Final",
            "LON",
            "LAT",
            "mass_balance_error",
            "Quality_Flag_Recomputed",
            "Fault_Dist",
        ]
    )
    bad_numeric = pd.Series(False, index=df.index)
    for column in sorted(numeric.intersection(df.columns)):
        original = df[column]
        converted = pd.to_numeric(original, errors="coerce")
        bad_numeric |= original.notna() & converted.isna()
        df[column] = converted
    # Carry malformed values to quarantine instead of silently changing them to missing.
    if policy == CURATED_POLICY and bad_numeric.any():
        raise ValueError("Malformed numeric values require review; curated measurements cannot be silently replaced.")
    df["_invalid_numeric"] = bad_numeric
    if df.ID_Final.isna().any() or ((df.ID_Final % 1) != 0).any():
        raise ValueError("ID_Final must contain nonmissing integer identifiers.")
    df["ID_Final"] = df.ID_Final.astype(int)
    repeated_rows = df[df.duplicated("ID_Final", keep="first")].copy()
    repeated_rows["QC_Reason"] = "spatial_join_duplicate"
    df = collapse_spatial_matches(df, SPATIAL)
    reasons = pd.Series("", index=df.index)

    def flag(mask, reason):
        reasons.loc[mask] = reasons.loc[mask].map(lambda v: f"{v};{reason}" if v else reason)

    flag(df.pop("_invalid_numeric"), "invalid_numeric_value")
    flag(df[CORE].isna().any(axis=1), "missing_core_oxide")
    analytical = [c for c in OXIDE_FEATURES_EXTENDED if c in df and c not in {"LOI", "Sum_Oxs"}]
    flag((df[analytical] < 0).any(axis=1) | (df[analytical] > 100).any(axis=1), "oxide_out_of_range")
    numeric_cols = df.select_dtypes(include="number").columns
    flag(pd.Series(np.isinf(df[numeric_cols].to_numpy(dtype=float)).any(axis=1), index=df.index), "infinite_value")
    flag(~df["ROCK TYPE"].isin(["VOL", "PLU"]), "invalid_domain")
    flag(df.ROCK_NAME.isna(), "missing_class")
    if "calc_error" in df:
        flag(df.calc_error.notna(), "cipw_calculation_error")
    if "mass_balance_error" in df:
        flag(df.mass_balance_error.isna() | (df.mass_balance_error.abs() > 0.10), "cipw_mass_balance_review")
    if "Quality_Flag_Recomputed" in df:
        flag(df.Quality_Flag_Recomputed.eq(2), "quality_flag_2")
    for column, low, high in (("LON", -180, 180), ("LAT", -90, 90)):
        if column in df:
            flag(df[column].notna() & ~df[column].between(low, high), "invalid_coordinate")
    # These are review flags, not authorization to remove already curated samples.
    chemistry = [c for c in OXIDE_FEATURES_EXTENDED if c in df]
    complete = df[CORE].notna().all(axis=1)
    labels = df["ROCK TYPE"].fillna("") + "::" + df.ROCK_NAME.fillna("")
    tagged = df[chemistry].copy()
    tagged["_label"] = labels
    conflicting = tagged.groupby(chemistry, dropna=False)["_label"].transform("nunique").gt(1)
    flag(complete & conflicting, "identical_chemistry_conflicting_labels")
    duplicate_key = ["Source", "LAB_ID", "ROCK TYPE", "ROCK_NAME", *chemistry]
    duplicate_key += [c for c in ["LON", "LAT"] if c in df]
    eligible = df[reasons.eq("")].sort_values("ID_Final")
    repeated_assays = eligible.duplicated(duplicate_key, keep="first")
    flag(df.index.isin(eligible.index[repeated_assays]), "duplicate_analysis")
    excluded = df[reasons.ne("")].copy() if policy == "restricted_experiment" else df.iloc[:0].copy()
    excluded["QC_Reason"] = reasons.reindex(excluded.index)
    kept = df.copy() if policy == CURATED_POLICY else df[reasons.eq("")].copy()
    kept["QC_Review"] = reasons.reindex(kept.index).fillna("")
    kept["Sample_Group"] = sample_groups(kept)
    kept = kept.sort_values("ID_Final").reset_index(drop=True)
    audit = pd.concat([repeated_rows.drop(columns=["_invalid_numeric"], errors="ignore"), excluded], ignore_index=True)
    report = {
        "input_rows": len(frame),
        "unique_input_ids": int(frame.ID_Final.nunique()),
        "spatial_duplicate_rows_removed": len(repeated_rows),
        "quarantined_or_duplicate_rows": len(excluded),
        "clean_rows": len(kept),
        "clean_unique_ids": int(kept.ID_Final.nunique()),
        "sample_groups": int(kept.Sample_Group.nunique()),
        "policy_id": policy,
        "review_rows_retained": int(kept.QC_Review.ne("").sum()),
        "review_reasons": kept.loc[kept.QC_Review.ne(""), "QC_Review"]
        .str.split(";")
        .explode()
        .value_counts()
        .to_dict(),
        "reasons": audit.QC_Reason.str.split(";").explode().value_counts().to_dict(),
        "trimmed_text_cells": changes,
        "missing_values": {c: int(v) for c, v in kept.isna().sum().items() if v},
        "ambiguous_spatial_attributes": {c: int(kept[c].sum()) for c in kept if c.endswith("_Ambiguous")},
        "policy": "No assay imputation, renormalization or lithological relabeling. "
        "Spatial join repetitions are collapsed by ID. All curated IDs are retained by default; "
        "duplicate analyses, label conflicts and CIPW balance checks are review warnings only. "
        "Ambiguous map attributes are missing and all candidates are preserved. "
        "Exclusion beyond spatial repeats requires the explicit restricted_experiment policy.",
    }
    if len(kept) + len(audit) != len(frame):
        raise AssertionError("Dataset row accounting failed.")
    return kept, audit, report


def write_clean_dataset(
    source: Path,
    output: Path,
    sheet: str = "training_ready_final",
    *,
    policy: str = CURATED_POLICY,
    reference: Path | None = None,
) -> dict:
    if source.resolve() == output.resolve():
        raise ValueError("The cleaned dataset must not overwrite its source.")
    if output.exists():
        raise FileExistsError(f"Output already exists; choose a new destination: {output}")
    for companion in (
        output.with_suffix(".csv"),
        output.with_suffix(".audit.json"),
        output.with_name(output.stem + "_excluded.csv"),
        output.with_name(output.stem + "_review.csv"),
    ):
        if companion.exists():
            raise FileExistsError(f"Output already exists: {companion}")
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    frame = pd.read_excel(source, sheet_name=sheet)
    clean, audit, report = clean_dataset(frame, policy=policy)
    if reference is not None:
        baseline_hash = hashlib.sha256(reference.read_bytes()).hexdigest()
        baseline = pd.read_excel(reference, sheet_name=sheet).set_index("ID_Final")
        candidate = clean.set_index("ID_Final")
        if not baseline.index.is_unique or set(baseline.index) != set(candidate.index):
            raise ValueError("Curated reference IDs do not match the output; no output was written.")
        pd.testing.assert_frame_equal(
            baseline.sort_index(),
            candidate[baseline.columns].sort_index(),
            check_dtype=False,
            check_exact=False,
            rtol=1e-12,
            atol=1e-12,
        )
        report["curated_reference"] = {
            "file": reference.name,
            "sha256": baseline_hash,
            "rows": len(baseline),
            "original_columns_verified": list(baseline.columns),
            "all_ids_and_original_values_preserved": True,
        }
    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise ValueError("Source workbook changed during cleaning; retry with a stable source.")
    report.update({"source_file": source.name, "source_sha256": source_hash, "source_sheet": sheet})
    output.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        clean.to_excel(writer, sheet_name="training_ready_final", index=False)
        audit.to_excel(writer, sheet_name="excluded_review", index=False)
        clean.loc[clean.QC_Review.ne("")].to_excel(writer, sheet_name="retained_review", index=False)
        clean.groupby(["ROCK TYPE", "ROCK_NAME"]).size().rename("count").reset_index().to_excel(
            writer, sheet_name="class_frequency", index=False
        )
    csv_path = output.with_suffix(".csv")
    clean.to_csv(csv_path, index=False, encoding="utf-8-sig")
    audit.to_csv(output.with_name(output.stem + "_excluded.csv"), index=False, encoding="utf-8-sig")
    clean.loc[clean.QC_Review.ne("")].to_csv(
        output.with_name(output.stem + "_review.csv"), index=False, encoding="utf-8-sig"
    )
    report["output_sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
    report["csv_sha256"] = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    output.with_suffix(".audit.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def ensure_clean_training_dataset(source: Path, directory: Path) -> Path:
    """Reuse an audited clean workbook or create a new copy keyed by source hash."""
    fingerprint = hashlib.sha256(source.read_bytes()).hexdigest()
    audit_path = source.with_suffix(".audit.json")
    if audit_path.exists():
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        if audit.get("output_sha256") != fingerprint:
            raise ValueError("Clean workbook has changed since its audit; regenerate a clean copy.")
        if audit.get("policy_id") != CURATED_POLICY:
            raise ValueError(
                "Restricted/legacy dataset is not the curated baseline; regenerate from the original source."
            )
        return source
    output = directory / f"GeoNormML_training_curated_{fingerprint[:12]}.xlsx"
    if output.exists():
        audit = json.loads(output.with_suffix(".audit.json").read_text(encoding="utf-8"))
        if (
            audit.get("source_sha256") != fingerprint
            or audit.get("policy_id") != CURATED_POLICY
            or audit.get("output_sha256") != hashlib.sha256(output.read_bytes()).hexdigest()
        ):
            raise ValueError("Existing cleaned copy does not match its audit.")
    else:
        write_clean_dataset(source, output)
    return output
