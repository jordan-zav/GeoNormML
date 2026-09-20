import geopandas as gpd
from shapely.geometry import Point, box

from scripts import spatial_join_dataset as spatial


def test_overlapping_belts_preserve_one_row_per_sample(monkeypatch, tmp_path):
    polygons = gpd.GeoDataFrame(
        {"franja": ["belt A", "belt B"]}, geometry=[box(0, 0, 3, 3), box(1, 1, 4, 4)], crs="EPSG:4326"
    )
    samples = gpd.GeoDataFrame(
        {"ID_Final": [1, 2], "SiO2": [55.0, 60.0]}, geometry=[Point(2, 2), Point(10, 10)], crs="EPSG:4326"
    )
    monkeypatch.setattr(spatial, "find_spatial_file", lambda *_args: tmp_path / "belts.gpkg")
    monkeypatch.setattr(spatial.gpd, "read_file", lambda *_args, **_kwargs: polygons)
    result = spatial._join_franjas(samples)
    assert len(result) == 2 and result.ID_Final.is_unique
    assert result.Metal_Belt.isna().all()
    assert result.loc[0, "Metal_Belt_Ambiguous"]
    assert result.loc[0, "SiO2"] == 55.0
    assert result.crs == samples.crs
