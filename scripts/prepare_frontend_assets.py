import json
from pathlib import Path
import rasterio
from shapely.geometry import box, mapping


# ============================================================
# Paths Setup
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEM_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "jezero"
    / "terrain"
    / "jezero_aoi_ctx_dem_20m.tif"
)

OUTPUT_GEOJSON = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "jezero"
    / "jezero_aoi_boundary.geojson"
)

OUTPUT_METADATA = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "jezero"
    / "map_metadata.json"
)


# ============================================================
# Extract Bounds, CRS, and Dimensions from DEM
# ============================================================

def prepare_assets():
    if not DEM_PATH.exists():
        raise FileNotFoundError(f"DEM file not found at: {DEM_PATH}")

    with rasterio.open(DEM_PATH) as src:
        bounds = src.bounds
        crs_string = src.crs.to_string() if src.crs else "IAU2000:49900"
        resolution = src.res[0]
        height, width = src.shape

    print(f"Loaded DEM successfully:")
    print(f" - Bounds: {bounds}")
    print(f" - CRS: {crs_string}")
    print(f" - Grid Size: {width} x {height}")

    # ============================================================
    # 1. Create AOI Boundary GeoJSON
    # ============================================================

    aoi_polygon = box(bounds.left, bounds.bottom, bounds.right, bounds.top)

    geojson_data = {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {
                "name": crs_string
            }
        },
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "name": "Jezero Crater 10x10km Operational Sector",
                    "description": "Active navigation grid for A* pathfinding engine",
                    "grid_rows": height,
                    "grid_cols": width,
                    "resolution_m": resolution
                },
                "geometry": mapping(aoi_polygon)
            }
        ]
    }

    OUTPUT_GEOJSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_GEOJSON, "w") as f:
        json.dump(geojson_data, f, indent=2)

    print(f"\n[✓] AOI Boundary GeoJSON saved to: {OUTPUT_GEOJSON}")

    # ============================================================
    # 2. Create Map Metadata JSON for Frontend Configuration
    # ============================================================

    metadata = {
        "project": "MarsWalk Intelligence",
        "region": "Jezero Crater",
        "crs": crs_string,
        "grid": {
            "rows": height,
            "cols": width,
            "resolution_meters": resolution
        },
        "bounds": {
            "min_x": bounds.left,
            "max_x": bounds.right,
            "min_y": bounds.bottom,
            "max_y": bounds.top
        },
        "center": {
            "x": (bounds.left + bounds.right) / 2.0,
            "y": (bounds.bottom + bounds.top) / 2.0
        }
    }

    with open(OUTPUT_METADATA, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"[✓] Frontend Map Metadata saved to: {OUTPUT_METADATA}")


if __name__ == "__main__":
    prepare_assets()
