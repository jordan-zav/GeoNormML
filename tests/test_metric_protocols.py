import numpy as np
import pandas as pd

from geonormml.quality import sample_groups
from scripts.audit_metric_protocols import diagnostic_folds


def test_protocol_control_exposes_replicate_overlap_without_losing_observations():
    frame = pd.DataFrame(
        {
            "ID_Final": range(80),
            "Source": "lab",
            "LAB_ID": [f"sample-{i // 2}" for i in range(80)],
            "ROCK TYPE": "VOL",
            "ROCK_NAME": ["a"] * 40 + ["b"] * 40,
        }
    )
    groups = sample_groups(frame)
    for grouped in (False, True):
        seen = np.zeros(len(frame), dtype=int)
        overlaps = []
        for train, valid in diagnostic_folds(frame, grouped):
            assert not set(train) & set(valid)
            assert set(train) | set(valid) == set(range(len(frame)))
            seen[valid] += 1
            overlaps.append(len(set(groups.iloc[train]) & set(groups.iloc[valid])))
        assert (seen == 1).all()
        assert max(overlaps) == 0 if grouped else max(overlaps) > 0
