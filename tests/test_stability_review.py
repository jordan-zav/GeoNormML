import numpy as np
import pandas as pd
import pytest

from scripts.review_stability_generation import verify_metrics, verify_splits


def test_independent_review_rejects_metric_drift():
    actual, predicted = ["a", "a", "b", "c"], ["a", "b", "b", "b"]
    metrics = {"accuracy": 0.5, "f1_macro": 7 / 18, "balanced_accuracy": 0.5, "mcc": 3 / np.sqrt(60)}
    verify_metrics(actual, predicted, ["a", "b", "c"], metrics)
    with pytest.raises(ValueError, match="accuracy"):
        verify_metrics(actual, predicted, ["a", "b", "c"], {**metrics, "accuracy": 0.75})


def test_review_rejects_replicates_even_when_ids_differ():
    frame = pd.DataFrame({"Sample_Group": ["same", "same", "other", "last"]})
    recorded = [{"train_ids": [0, 2], "valid_ids": [1, 3]}]
    with pytest.raises(ValueError, match="Replicate leakage"):
        verify_splits(frame, frame, recorded, [(np.array([0, 2]), np.array([1, 3]))])
