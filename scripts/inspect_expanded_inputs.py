"""Print aggregate input coverage before freezing the expanded benchmark plan."""

import json

from geonormml.data import load_training_dataset
from geonormml.features import FEATURE_SETS

if __name__ == "__main__":
    data = load_training_dataset()
    print(json.dumps({
        "rows": len(data),
        "families": {name: {
            "missing_columns": [c for c in spec.columns if c not in data],
            "all_missing_columns": [c for c in spec.columns if c in data and data[c].isna().all()],
        } for name, spec in FEATURE_SETS.items()},
        "domains": data["ROCK TYPE"].value_counts().to_dict(),
        "series": data.Serie_Mag.value_counts(dropna=False).to_dict(),
    }, indent=2))
