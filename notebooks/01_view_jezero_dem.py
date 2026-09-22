import rasterio
import numpy as np
import matplotlib.pyplot as plt


path = "data/raw/jezero/ctx_dem/M20_JezeroCrater_CTXDEM_20m.tif"

with rasterio.open(path) as ds:

    # Read DEM while automatically masking NoData values
    dem = ds.read(1, masked=True)

    print("Shape:", dem.shape)
    print("NoData value:", ds.nodata)
    print("Min elevation:", dem.min())
    print("Max elevation:", dem.max())
    print("Mean elevation:", dem.mean())


plt.figure(figsize=(10, 8))

plt.imshow(dem)

plt.title("Jezero Crater - CTX DEM")
plt.xlabel("X pixels")
plt.ylabel("Y pixels")

plt.colorbar(label="Elevation")

plt.show()