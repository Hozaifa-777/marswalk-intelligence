import os

import rasterio
import numpy as np

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt


# ==========================================
# Paths
# ==========================================

input_path = (
    "data/processed/jezero/terrain/"
    "jezero_aoi_ctx_dem_20m.tif"
)

output_dir = "data/sample"
os.makedirs(output_dir, exist_ok=True)

output_path = os.path.join(
    output_dir,
    "jezero_aoi_terrain_cost.png"
)


# ==========================================
# Read AOI DEM
# ==========================================

with rasterio.open(input_path) as ds:

    dem = ds.read(1).astype(np.float64)

    nodata = ds.nodata
    resolution = ds.res[0]


print("Resolution:", resolution)
print("NoData:", nodata)


# ==========================================
# Handle NoData
# ==========================================

dem[dem == nodata] = np.nan


# ==========================================
# Calculate slope
# ==========================================

dy, dx = np.gradient(
    dem,
    resolution,
    resolution
)

slope_radians = np.arctan(
    np.hypot(dx, dy)
)

slope_degrees = np.degrees(
    slope_radians
)

slope_degrees[np.isnan(dem)] = np.nan


# ==========================================
# Slope statistics
# ==========================================

print("Minimum slope:",
      np.nanmin(slope_degrees))

print("Maximum slope:",
      np.nanmax(slope_degrees))

print("Mean slope:",
      np.nanmean(slope_degrees))

print("90th percentile:",
      np.nanpercentile(slope_degrees, 90))

print("95th percentile:",
      np.nanpercentile(slope_degrees, 95))


# ==========================================
# Terrain Cost
# ==========================================

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

terrain_cost[np.isnan(slope_degrees)] = np.nan


# ==========================================
# Cost statistics
# ==========================================

print("Reference slope:",
      reference_slope)

print("Minimum cost:",
      np.nanmin(terrain_cost))

print("Maximum cost:",
      np.nanmax(terrain_cost))

print("Mean cost:",
      np.nanmean(terrain_cost))


# ==========================================
# Visualization
# ==========================================

plt.figure(figsize=(10, 8))

plt.imshow(terrain_cost)

plt.title(
    "Jezero AOI - Terrain Cost"
)

plt.xlabel("X pixels")
plt.ylabel("Y pixels")

plt.colorbar(
    label="Terrain Cost"
)

plt.tight_layout()

plt.savefig(
    output_path,
    dpi=150,
    bbox_inches="tight"
)

plt.close()


print()
print("Image saved successfully:")
print(output_path)