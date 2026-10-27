import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import accuracy_score, f1_score, matthews_corrcoef

from geonormml.expanded import paired_diagnostic, profile_frame, score_arrays, specifications


def test_expanded_scope_covers_catalog_without_spatial_primary_selection():
    specs = specifications()
    assert len(specs) == 147 and len({s["id"] for s in specs}) == 147
    primary = [s for s in specs if s["scope"] == "transfer_candidate"]
    assert len(primary) == 120
    assert {s["algorithm"] for s in primary} == {"SVM_PCA", "RandomForest", "XGBoost"}
    assert all("spatial" not in s["family"] and "geodata" not in s["family"]
               and s["family"] != "combined_full" for s in primary)


def test_profile_indices_replace_historical_values_and_add_fluorapatite():
    data = pd.DataFrame({"SiO2": [50.0], "Na2O": [2.0], "K2O": [2.0],
                         "Al2O3": [15.0], "CaO": [8.0], "MgO": [7.0], "FeOT": [9.0],
                         "%An en Pl": [999.0], "SUM_QAP": [999.0], "Serie_Mag": ["old"]}, index=[42])
    norms = pd.DataFrame({"phase_An": [10.0], "phase_Ab": [30.0], "phase_Or": [20.0],
                          "phase_Q": [5.0], "phase_Ap": [1.0], "phase_FAp": [2.0]}, index=[42])
    changed = profile_frame(data, norms)
    assert changed.loc[42, "%An en Pl"] == 25
    assert changed.loc[42, "SUM_QAP"] == 65
    assert changed.loc[42, "Ap"] == 3
    assert changed.loc[42, "Serie_Mag"] != "old"
    assert data.loc[42, "SUM_QAP"] == 999


def test_fast_metrics_match_reference_and_group_swap_has_correct_null():
    actual = np.array([0, 0, 1, 1, 2, 2])
    predicted = np.array([0, 1, 1, 1, 0, 2])
    result = score_arrays(actual, predicted, 4)
    assert result["accuracy"] == accuracy_score(actual, predicted)
    assert result["f1_macro"] == pytest.approx(
        f1_score(actual, predicted, labels=[0, 1, 2, 3], average="macro", zero_division=0)
    )
    assert result["mcc"] == pytest.approx(matthews_corrcoef(actual, predicted))
    comparison = paired_diagnostic(actual, predicted, predicted, ["a", "a", "b", "b", "c", "c"], 3, repeats=19)
    assert comparison["delta_macro_f1"] == 0
    assert comparison["two_sided_group_swap_p"] == 1
    assert comparison["groups"] == 3
