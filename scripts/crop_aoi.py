import os

import rasterio
from rasterio.windows import from_bounds


# ==========================================
# Input / Output
# ==========================================

input_path = (
    "data/raw/jezero/ctx_dem/"
    "M20_JezeroCrater_CTXDEM_20m.tif"
)

output_dir = "data/processed/jezero/terrain"
os.makedirs(output_dir, exist_ok=True)

output_path = os.path.join(
    output_dir,
    "jezero_aoi_ctx_dem_20m.tif"
)


# ==========================================
# AOI
# ==========================================

# First test AOI: approximately 10 km × 10 km
#
# These coordinates are in the DEM's
# Jezero projected coordinate system.

min_x = 4_350_000
max_x = 4_360_000

min_y = 1_090_000
max_y = 1_100_000


# ==========================================
# Read and crop
# ==========================================

with rasterio.open(input_path) as src:

    print("Original size:")
    print(src.width, "x", src.height)

    print("Original bounds:")
    print(src.bounds)

    print("CRS:")
    print(src.crs)

    window = from_bounds(
        min_x,
        min_y,
        max_x,
        max_y,
        transform=src.transform
    )

    # Make sure we only request valid pixels
    window = window.round_offsets().round_lengths()

    data = src.read(1, window=window)

    transform = src.window_transform(window)

    profile = src.profile.copy()

    profile.update(
        width=data.shape[1],
        height=data.shape[0],
        transform=transform
    )


# ==========================================
# Save cropped DEM
# ==========================================

with rasterio.open(output_path, "w", **profile) as dst:

    dst.write(data, 1)


print()
print("AOI created successfully!")
print("Output:", output_path)
print("Size:", data.shape[1], "x", data.shape[0])
print("Resolution:", profile["transform"].a)