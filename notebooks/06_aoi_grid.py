import rasterio
import numpy as np

# =========================
# Paths
# =========================

dem_path = "data/processed/jezero/terrain/jezero_aoi_ctx_dem_20m.tif"


# =========================
# Load DEM
# =========================

with rasterio.open(dem_path) as src:

    dem = src.read(1).astype(np.float64)

    transform = src.transform
    resolution = src.res[0]
    nodata = src.nodata

    print("Grid size:", dem.shape)
    print("Resolution:", resolution)
    print("NoData:", nodata)


# =========================
# Valid cells
# =========================

valid_mask = dem != nodata

print("Total cells:", dem.size)
print("Valid cells:", np.sum(valid_mask))
print("Blocked cells:", np.sum(~valid_mask))


# =========================
# Calculate slope
# =========================

dem_clean = dem.copy()
dem_clean[~valid_mask] = np.nan

dy, dx = np.gradient(
    dem_clean,
    resolution,
    resolution
)

slope_radians = np.arctan(
    np.hypot(dx, dy)
)

slope_degrees = np.degrees(slope_radians)

slope_degrees[~valid_mask] = np.nan


# =========================
# Terrain Cost
# =========================

reference_slope = np.nanpercentile(
    slope_degrees,
    95
)

normalized_slope = (
    slope_degrees / reference_slope
)

normalized_slope = np.clip(
    normalized_slope,
    0,
    1
)

terrain_cost = (
    1 + normalized_slope ** 2
)

terrain_cost[~valid_mask] = np.inf


# =========================
# Grid Information
# =========================

print("\nTerrain Grid Ready")

print("Minimum terrain cost:",
      np.nanmin(terrain_cost))

print("Maximum terrain cost:",
      np.nanmax(
          terrain_cost[
              np.isfinite(terrain_cost)
          ]
      ))

print("Reference slope:",
      reference_slope)