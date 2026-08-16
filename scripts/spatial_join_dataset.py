"""Spatial join: enrich the training dataset with geological map and fault data.

Performs an automated spatial intersection of sample locations against
INGEMMET shapefiles (geology 100k, faults) placed in ``Dataset/raw/spatial/``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

from geonormml.config import DATASET_DIR, CONSISTENT_DATASET, DATASET_SHEET, PROJECT_ROOT, setup_logging

logger = setup_logging("spatial_join")

# =============================================================================
# PATHS (portable — derived from PROJECT_ROOT)
# =============================================================================
# Prioritize Dataset/GIS (user downloaded directory), fallback to Dataset/raw/spatial
SPATIAL_DIR = PROJECT_ROOT / "Dataset" / "GIS"
if not SPATIAL_DIR.exists():
    SPATIAL_DIR = PROJECT_ROOT / "Dataset" / "raw" / "spatial"

OUTPUT_PATH = DATASET_DIR / "Merge_Filtered_training_ready_v5_spatial.xlsx"


# =============================================================================
# AUTO-DETECTION HELPERS
# =============================================================================

def find_spatial_file(directory: Path, keywords: list[str]) -> Path | None:
    """Find the first geo-file whose name contains any *keyword*, searching recursively."""
    if not directory.exists():
        return None

    # Search recursively with rglob
    for ext in ("**/*.shp", "**/*.gpkg", "**/*.geojson"):
        for fp in directory.rglob(ext):
            name_lower = fp.name.lower()
            if any(kw in name_lower for kw in keywords):
                return fp
    return None


def auto_detect_column(columns: list[str], keywords: list[str]) -> str | None:
    """Case-insensitive column name matcher."""
    for kw in keywords:
        for col in columns:
            if kw in col.lower():
                return col
    return None


def parse_age_from_symbol(symbol: str) -> str:
    """Infer the geological age classification from standard INGEMMET codes."""
    if not isinstance(symbol, str) or not symbol:
        return "Unknown"
    
    # Check prefixes in order of specificity
    if symbol.startswith("Qh") or symbol.startswith("Qp") or symbol.startswith("Q"):
        return "Quaternary"
    elif symbol.startswith("NQ"):
        return "Neogene-Quaternary"
    elif symbol.startswith("Nm") or symbol.startswith("Np") or symbol.startswith("N"):
        return "Neogene"
    elif symbol.startswith("PN"):
        return "Paleogene-Neogene"
    elif symbol.startswith("Po") or symbol.startswith("Pe") or symbol.startswith("Pa"):
        return "Paleogene"
    elif symbol.startswith("Ks") or symbol.startswith("Ki") or symbol.startswith("K"):
        return "Cretaceous"
    elif symbol.startswith("Js") or symbol.startswith("Ji") or symbol.startswith("J"):
        return "Jurassic"
    elif symbol.startswith("Ts") or symbol.startswith("Ti") or symbol.startswith("T"):
        return "Triassic"
    elif symbol.startswith("P-") or symbol == "P":
        return "Permian"
    elif symbol.startswith("PET") or symbol.startswith("PE"):
        return "Precambrian"
    elif symbol.startswith("C"):
        return "Carboniferous"
    elif symbol.startswith("D"):
        return "Devonian"
    elif symbol.startswith("S"):
        return "Silurian"
    elif symbol.startswith("O"):
        return "Ordovician"
    
    # Case-insensitive general checks
    symbol_upper = symbol.upper()
    if symbol_upper.startswith("Q"):
        return "Quaternary"
    elif symbol_upper.startswith("N"):
        return "Neogene"
    elif symbol_upper.startswith("K"):
        return "Cretaceous"
    elif symbol_upper.startswith("J"):
        return "Jurassic"
    elif symbol_upper.startswith("T"):
        return "Triassic"
    elif symbol_upper.startswith("P"):
        if any(x in symbol for x in ("e", "a", "o")):
            return "Paleogene"
        return "Permian"
    
    return "Unknown"


def get_utm_zone_peru(lon: float) -> str:
    """Calculate the UTM zone for a longitude within Peruvian territory."""
    if pd.isna(lon):
        return "Unknown"
    if -84.0 <= lon < -78.0:
        return "17S"
    if -78.0 <= lon < -72.0:
        return "18S"
    if -72.0 <= lon < -66.0:
        return "19S"
    zone_num = int((lon + 180) / 6) + 1
    return f"{zone_num}S"


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def main() -> None:
    logger.info("=== GeoNormML: Spatial Join and Geoprocessing ===")

    # --- Validate inputs ---------------------------------------------------
    if not CONSISTENT_DATASET.exists():
        logger.error("Training dataset not found: %s", CONSISTENT_DATASET)
        sys.exit(1)

    SPATIAL_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load training dataset
    logger.info("Loading training dataset: %s", CONSISTENT_DATASET.name)
    df = pd.read_excel(CONSISTENT_DATASET, sheet_name=DATASET_SHEET)
    logger.info("Loaded %d samples.", len(df))

    # Validate required coordinate columns
    missing_coords = [c for c in ("LON", "LAT") if c not in df.columns]
    if missing_coords:
        logger.error("Dataset is missing coordinate columns: %s", missing_coords)
        sys.exit(1)

    # 2. Calculate UTM zones
    logger.info("Calculating UTM zones...")
    df["UTM_Zone"] = df["LON"].apply(get_utm_zone_peru)
    logger.info("UTM zone distribution:\n%s", df["UTM_Zone"].value_counts().to_string())

    # 3. Convert to GeoDataFrame (WGS84)
    logger.info("Creating GeoDataFrame (EPSG:4326)...")
    gdf_samples = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["LON"], df["LAT"]),
        crs="EPSG:4326",
    )

    # 4. Geology 50k / 100k intersection
    gdf_samples = _join_geology(gdf_samples)

    # 4b. Franjas (Metallogenetic belts) intersection
    gdf_samples = _join_franjas(gdf_samples)

    # 5. Fault distance
    gdf_samples = _compute_fault_distance(gdf_samples)

    # 6. Export
    _export_result(gdf_samples)

    logger.info("=== Spatial join completed successfully ===")


# =============================================================================
# GEOLOGY JOIN
# =============================================================================

def _join_geology(gdf_samples: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Spatial-join sample points with 50k (prioritized) or 100k geology map."""
    # Prioritize 50k geodata, fall back to 100k or generic map
    geology_path = find_spatial_file(SPATIAL_DIR, ["50k"])
    if geology_path is None:
        geology_path = find_spatial_file(SPATIAL_DIR, ["geol", "100k", "map"])

    if geology_path is None:
        logger.warning("[SKIP] Geology layer not found in %s", SPATIAL_DIR)
        return gdf_samples

    logger.info("[FOUND] Geology file: %s", geology_path.name)
    
    # Bbox spatial filter optimization with CRS projection
    try:
        # Read 1 row to get file CRS dynamically
        meta = gpd.read_file(geology_path, rows=1)
        file_crs = meta.crs
        
        # Project samples to file CRS to compute correct bounding box
        gdf_samples_proj = gdf_samples.to_crs(file_crs)
        minx, miny, maxx, maxy = gdf_samples_proj.geometry.x.min(), gdf_samples_proj.geometry.y.min(), gdf_samples_proj.geometry.x.max(), gdf_samples_proj.geometry.y.max()
        
        # Buffer around sample points (10km if projected in meters, 0.1 deg if geographic)
        buffer = 10000.0 if gdf_samples_proj.crs.is_projected else 0.1
        bbox = (minx - buffer, miny - buffer, maxx + buffer, maxy + buffer)
        
        logger.info("  Loading geology with projected filter (bbox: %s, CRS: %s)...", bbox, file_crs)
        gdf_geol = gpd.read_file(geology_path, bbox=bbox)
    except Exception as exc:
        logger.warning("  Spatial filter read failed, loading full geology file: %s", exc)
        gdf_geol = gpd.read_file(geology_path)

    logger.info("  Geology polygons: %d | CRS: %s", len(gdf_geol), gdf_geol.crs)

    # Remove invalid/empty geometries
    n_before = len(gdf_geol)
    gdf_geol = gdf_geol[gdf_geol.geometry.notna() & gdf_geol.geometry.is_valid]
    n_dropped = n_before - len(gdf_geol)
    if n_dropped > 0:
        logger.warning("  Dropped %d invalid/empty geology polygons.", n_dropped)

    # Reproject to WGS84 geographic coordinates
    if gdf_geol.crs != "EPSG:4326":
        logger.info("  Reprojecting geology from %s → EPSG:4326...", gdf_geol.crs)
        gdf_geol = gdf_geol.to_crs("EPSG:4326")

    # Auto-detect relevant columns
    cols = list(gdf_geol.columns)
    unit_col = auto_detect_column(cols, ["unidad", "unid", "unit", "form", "nomb", "sigla", "cod"])
    age_col = auto_detect_column(cols, ["edad", "cron", "era", "perio", "epoch", "sistem"])
    lith_col = auto_detect_column(cols, ["lito", "roc", "desc", "tipo"])

    # Fallback: Parse age from symbol/sigla column if no explicit age column is found
    if not age_col:
        sigla_col = auto_detect_column(cols, ["sigla", "symb", "code", "name"])
        if sigla_col:
            logger.info("  Age column not found. Parsing geological age from symbol column '%s'...", sigla_col)
            gdf_geol["Geol_Age_100k_parsed"] = gdf_geol[sigla_col].apply(parse_age_from_symbol)
            age_col = "Geol_Age_100k_parsed"

    logger.info("  Column detection → Unit: %s | Age: %s | Litho: %s",
                unit_col or "—", age_col or "—", lith_col or "—")

    cols_to_keep = [c for c in (unit_col, age_col, lith_col) if c]
    if not cols_to_keep:
        logger.warning("  No usable attribute columns found. Skipping geology join.")
        return gdf_samples

    gdf_geol_filtered = gdf_geol[["geometry"] + cols_to_keep]

    logger.info("  Performing spatial join (within)...")
    gdf_joined = gpd.sjoin(gdf_samples, gdf_geol_filtered, how="left", predicate="within")

    if "index_right" in gdf_joined.columns:
        gdf_joined = gdf_joined.drop(columns=["index_right"])

    # Rename to unified GeoNormML names
    rename_map = {}
    if unit_col and unit_col in gdf_joined.columns:
        rename_map[unit_col] = "Geol_Unit"
    if age_col and age_col in gdf_joined.columns:
        rename_map[age_col] = "Geol_Age_100k"
    if lith_col and lith_col in gdf_joined.columns:
        rename_map[lith_col] = "Geol_Lith_100k"

    if rename_map:
        gdf_joined = gdf_joined.rename(columns=rename_map)
        logger.info("  Added geology columns: %s", list(rename_map.values()))

    return gdf_joined


def _join_franjas(gdf_samples: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Spatial-join sample points with metallogenetic belt map."""
    franjas_path = find_spatial_file(SPATIAL_DIR, ["franja", "metal"])

    if franjas_path is None:
        logger.warning("[SKIP] Metallogenetic belts layer not found in %s", SPATIAL_DIR)
        return gdf_samples

    logger.info("[FOUND] Metallogenetic belts file: %s", franjas_path.name)
    
    # Load with spatial filter (bbox) optimization
    try:
        # Read 1 row to get file CRS
        meta = gpd.read_file(franjas_path, rows=1)
        file_crs = meta.crs
        
        # Project samples to file CRS
        gdf_samples_proj = gdf_samples.to_crs(file_crs)
        minx, miny, maxx, maxy = gdf_samples_proj.geometry.x.min(), gdf_samples_proj.geometry.y.min(), gdf_samples_proj.geometry.x.max(), gdf_samples_proj.geometry.y.max()
        buffer = 10000.0 if gdf_samples_proj.crs.is_projected else 0.1
        bbox = (minx - buffer, miny - buffer, maxx + buffer, maxy + buffer)
        
        logger.info("  Loading franjas with spatial filter (bbox: %s, CRS: %s)...", bbox, file_crs)
        gdf_franjas = gpd.read_file(franjas_path, bbox=bbox)
    except Exception as exc:
        logger.warning("  Spatial filter read failed, loading full franjas file: %s", exc)
        gdf_franjas = gpd.read_file(franjas_path)

    logger.info("  Franjas polygons: %d | CRS: %s", len(gdf_franjas), gdf_franjas.crs)

    # Remove invalid/empty geometries
    gdf_franjas = gdf_franjas[gdf_franjas.geometry.notna() & gdf_franjas.geometry.is_valid]

    # Reproject to WGS84 geographic coordinates
    if gdf_franjas.crs != "EPSG:4326":
        logger.info("  Reprojecting franjas from %s → EPSG:4326...", gdf_franjas.crs)
        gdf_franjas = gdf_franjas.to_crs("EPSG:4326")

    # Auto-detect relevant columns
    cols = list(gdf_franjas.columns)
    franja_col = auto_detect_column(cols, ["franja", "belt", "nombre", "nom"])

    if not franja_col:
        logger.warning("  No usable franja column found. Skipping franjas join.")
        return gdf_samples

    logger.info("  Performing spatial join (within) for franjas...")
    gdf_joined = gpd.sjoin(gdf_samples, gdf_franjas[["geometry", franja_col]], how="left", predicate="within")

    if "index_right" in gdf_joined.columns:
        gdf_joined = gdf_joined.drop(columns=["index_right"])

    gdf_joined = gdf_joined.rename(columns={franja_col: "Metal_Belt"})
    logger.info("  Added Metal_Belt column.")

    return gdf_joined


# =============================================================================
# FAULT DISTANCE
# =============================================================================

def _compute_fault_distance(gdf_samples: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Compute distance to the nearest fault in kilometres."""
    faults_path = find_spatial_file(SPATIAL_DIR, ["falla", "fault", "struct"])

    if faults_path is None:
        logger.warning("[SKIP] Faults layer not found in %s", SPATIAL_DIR)
        logger.warning("       Place files containing 'falla' or 'fault' in the folder.")
        return gdf_samples

    logger.info("[FOUND] Faults file: %s", faults_path.name)
    gdf_faults = gpd.read_file(faults_path)
    logger.info("  Fault features: %d | CRS: %s", len(gdf_faults), gdf_faults.crs)

    # Remove invalid/empty geometries
    n_before = len(gdf_faults)
    gdf_faults = gdf_faults[gdf_faults.geometry.notna() & gdf_faults.geometry.is_valid]
    n_dropped = n_before - len(gdf_faults)
    if n_dropped > 0:
        logger.warning("  Dropped %d invalid/empty fault geometries.", n_dropped)

    # Project to UTM 18S for metric distance
    logger.info("  Reprojecting to EPSG:32718 (UTM 18S) for metric distances...")
    gdf_samples_proj = gdf_samples.to_crs("EPSG:32718")
    gdf_faults_proj = gdf_faults.to_crs("EPSG:32718")

    logger.info("  Computing nearest-fault distances (sjoin_nearest)...")
    gdf_nearest = gpd.sjoin_nearest(
        gdf_samples_proj,
        gdf_faults_proj[["geometry"]],
        how="left",
        distance_col="distance_m",
    )

    # Deduplicate (multiple equidistant faults)
    gdf_nearest = gdf_nearest.reset_index()
    gdf_nearest = gdf_nearest.drop_duplicates(subset=["index"], keep="first")
    gdf_nearest = gdf_nearest.set_index("index")

    # Store in km on original GeoDataFrame
    gdf_samples["Fault_Dist"] = gdf_nearest["distance_m"] / 1000.0
    logger.info("  Fault_Dist (km) — %s", gdf_samples["Fault_Dist"].describe().to_string())

    return gdf_samples


# =============================================================================
# EXPORT
# =============================================================================

def _export_result(gdf_samples: gpd.GeoDataFrame) -> None:
    """Write the enriched dataset to Excel, preserving metadata sheets."""
    logger.info("Preparing export...")
    df_output = pd.DataFrame(gdf_samples.drop(columns=["geometry"], errors="ignore"))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Saving to: %s", OUTPUT_PATH)

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        df_output.to_excel(writer, sheet_name="training_ready_final", index=False)

        # Copy secondary sheets from original file
        try:
            xls_orig = pd.ExcelFile(CONSISTENT_DATASET)
            for sheet in xls_orig.sheet_names:
                if sheet != DATASET_SHEET:
                    sheet_df = pd.read_excel(CONSISTENT_DATASET, sheet_name=sheet)
                    sheet_df.to_excel(writer, sheet_name=sheet, index=False)
            logger.info("Copied metadata sheets from original dataset.")
        except Exception as exc:
            logger.warning("Could not copy extra sheets: %s", exc)

    logger.info("Enriched dataset saved: %s", OUTPUT_PATH)
    logger.info("To use in training, update DATASET_PATH in config.py.")


if __name__ == "__main__":
    main()
