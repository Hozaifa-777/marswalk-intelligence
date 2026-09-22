import os
import rasterio
import numpy as np

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt


# =========================
# Paths
# =========================

input_path = "data/raw/jezero/ctx_dem/M20_JezeroCrater_CTXDEM_20m.tif"

output_dir = "data/sample"
os.makedirs(output_dir, exist_ok=True)

output_path = os.path.join(
    output_dir,
    "jezero_slope.png"
)


# =========================
# Read DEM
# =========================

with rasterio.open(input_path) as ds:

    dem = ds.read(1).astype(np.float64)

    nodata = ds.nodata
    resolution = ds.res[0]

    print("NoData:", nodata)
    print("Resolution:", resolution)


# =========================
# Handle NoData
# =========================

dem[dem == nodata] = np.nan


# =========================
# Calculate slope
# =========================

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


# Remove invalid areas
slope_degrees[np.isnan(dem)] = np.nan


# =========================
# Statistics
# =========================

print("Minimum slope:", np.nanmin(slope_degrees))
print("Maximum slope:", np.nanmax(slope_degrees))
print("Mean slope:", np.nanmean(slope_degrees))

print("50th percentile:",
      np.nanpercentile(slope_degrees, 50))

print("90th percentile:",
      np.nanpercentile(slope_degrees, 90))

print("95th percentile:",
      np.nanpercentile(slope_degrees, 95))

print("99th percentile:",
      np.nanpercentile(slope_degrees, 99))


# =========================
# Create image
# =========================

plt.figure(figsize=(10, 8))

plt.imshow(slope_degrees)

plt.title("Jezero Crater - Slope")

plt.xlabel("X pixels")
plt.ylabel("Y pixels")

plt.colorbar(
    label="Slope (degrees)"
)

plt.tight_layout()


# =========================
# Save image
# =========================

plt.savefig(
    output_path,
    dpi=150,
    bbox_inches="tight"
)

plt.close()

print()
print("Image saved successfully:")
print(output_path)