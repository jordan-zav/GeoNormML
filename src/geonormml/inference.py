"""Row-preserving inference with an explicit chemistry or prepared-feature contract."""

import numpy as np
import pandas as pd

from .models import CALIBRATION_NOTE, LoadedModel, ModelError, load_model

MAJORS = ("SiO2", "TiO2", "Al2O3", "FeOT", "CaO", "MgO", "MnO", "Na2O", "K2O", "P2O5")
OPTIONAL_NORM = ("CO2", "F", "Cl", "SO3", "S", "ZrO2", "Cr2O3")


def _prepare_frame(data, manifest):
    """Return selected features and per-row errors, retaining positional row identity."""
    if not isinstance(data, pd.DataFrame) or data.columns.duplicated().any():
        raise ModelError("invalid_input", "Expected a DataFrame with unique column names")
    frame = data.reset_index(drop=True).copy(deep=True)
    errors = pd.Series("", index=frame.index, dtype=object)
    required = list(MAJORS) if manifest["input_mode"] == "oxide_chemistry" else manifest["feature_columns"]
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise ModelError("missing_columns", "Missing input columns: " + ", ".join(missing))
    categories = manifest.get("categorical_columns", [])
    numeric = (
        list(MAJORS) + list(OPTIONAL_NORM) + ["LOI", "Sum_Oxs"]
        if manifest["input_mode"] == "oxide_chemistry"
        else [name for name in required if name not in categories]
    )
    for name in numeric:
        if name not in frame:
            continue
        raw = frame[name].replace(r"^\s*$", np.nan, regex=True)
        values = pd.to_numeric(raw, errors="coerce")
        invalid = (
            (raw.notna() & values.isna())
            | np.isinf(values)
            | raw.map(lambda value: isinstance(value, (bool, np.bool_)))
        )
        errors.loc[invalid] = "invalid_numeric_input"
        frame[name] = values.astype(float)
    if "ROCK TYPE" in frame:
        errors.loc[frame["ROCK TYPE"].ne(manifest["domain_code"])] = "domain_mismatch"
    if manifest["input_mode"] == "prepared_features":
        for name in categories:
            frame[name] = frame[name].astype(object).where(frame[name].notna(), np.nan)
        return frame[required], errors

    missing_major = frame[list(MAJORS)].isna().any(axis=1)
    errors.loc[missing_major & errors.eq("")] = "missing_major"
    chemical = [name for name in (*MAJORS, *OPTIONAL_NORM) if name in frame]
    errors.loc[frame[chemical].lt(0).any(axis=1) & errors.eq("")] = "negative_oxide"
    # Only chemical inputs and measured auxiliaries enter derivation. Old norms,
    # categories, coordinates or column aliases are never silently reused.
    frame = frame[[name for name in (*MAJORS, *OPTIONAL_NORM, "LOI", "Sum_Oxs") if name in frame]].copy()
    for name in ("LOI", "Sum_Oxs"):
        if name not in frame:
            frame[name] = np.nan
    if manifest["feature_set"] == "oxides_core":
        return frame[manifest["feature_columns"]], errors

    from geonormpy import cipw

    from .expanded import profile_frame

    contract = manifest["normative"]
    records, positions = [], []
    for position in frame.index[errors.eq("")]:
        row = frame.loc[position]
        inputs = {name: float(row[name]) for name in (*MAJORS, *OPTIONAL_NORM) if name in row and pd.notna(row[name])}
        try:
            norm = cipw(
                inputs,
                profile=contract["profile"],
                iron_policy="fixed",
                fe3_fraction=contract["fe3_fraction"],
                carbonate_mode="calcite",
                strict=False,
                mass_tol=1e-6,
            )
        except ValueError as error:
            errors.at[position] = "normative_error:" + getattr(error, "code", "invalid_input")
            continue
        if not norm["flags"]["calculation_complete"]:
            errors.at[position] = "incomplete_norm"
            continue
        records.append({"phase_" + name: value for name, value in norm["minerals_wtpercent"].items()})
        positions.append(position)
    output = pd.DataFrame(index=frame.index, columns=manifest["feature_columns"], dtype=float)
    if positions:
        norms = pd.DataFrame(records, index=positions)
        prepared = profile_frame(frame.loc[positions], norms)
        # Context categories must remain their exact training strings, not codes.
        for column in manifest["feature_columns"]:
            if column in ("Clase_SiO2", "Serie_Mag"):
                output[column] = output[column].astype(object)
            output.loc[positions, column] = prepared[column]
    return output, errors


def predict_frame(data, model, *, id_column=None):
    """Predict supported rows; report rejected rows without silently dropping them."""
    manifest = model.manifest
    features, errors = _prepare_frame(data, manifest)
    if id_column is not None and id_column not in data:
        raise ModelError("missing_columns", f"Missing identifier column: {id_column}")
    labels = manifest["classes"]
    output = pd.DataFrame(
        {
            "input_row": np.arange(len(data)),
            "prediction": pd.Series([None] * len(data), dtype=object),
            "status": np.where(errors.eq(""), "predicted", "rejected"),
            "error_code": errors.to_numpy(),
        }
    )
    if id_column is not None:
        output.insert(1, "sample_id", data[id_column].to_numpy(copy=True))
    for label in labels:
        output["probability::" + label] = np.nan
    positions = features.index[errors.eq("")]
    if len(positions):
        try:
            predictions = np.asarray(model.estimator.predict(features.loc[positions]))
            if predictions.shape != (len(positions),):
                raise ModelError("invalid_prediction", "Estimator returned an unexpected prediction shape")
            if manifest.get("prediction_encoding", "encoded") == "encoded":
                if not np.isin(predictions, np.arange(len(labels))).all():
                    raise ModelError("invalid_prediction", "Estimator returned an unknown encoded class")
                predictions = np.asarray(labels, dtype=object)[predictions.astype(int)]
            elif not np.isin(predictions, labels).all():
                raise ModelError("invalid_prediction", "Estimator returned an unknown class label")
            output.loc[positions, "prediction"] = predictions
            if callable(getattr(model.estimator, "predict_proba", None)):
                probabilities = np.asarray(model.estimator.predict_proba(features.loc[positions]), dtype=float)
                if (
                    probabilities.shape != (len(positions), len(labels))
                    or not np.isfinite(probabilities).all()
                    or (probabilities < 0).any()
                    or (probabilities > 1).any()
                    or not np.allclose(probabilities.sum(axis=1), 1, atol=1e-6)
                ):
                    raise ModelError("invalid_prediction", "Estimator returned invalid class probabilities")
                output.loc[positions, ["probability::" + label for label in labels]] = probabilities
        except ModelError:
            raise
        except Exception as error:
            raise ModelError("prediction_failed", str(error)) from error
    output.index = data.index.copy()
    output.attrs.update(
        generation_id=manifest["generation_id"],
        domain_code=manifest["domain_code"],
        input_mode=manifest["input_mode"],
        note=CALIBRATION_NOTE,
    )
    return output


def predict(data, model, *, trusted=False, id_column=None):
    """Predict from a LoadedModel or an explicitly trusted manifest path."""
    loaded = model if isinstance(model, LoadedModel) else load_model(model, trusted=trusted)
    return predict_frame(data, loaded, id_column=id_column)
