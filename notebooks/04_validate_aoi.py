import rasterio
import numpy as np

path = (
    "data/processed/jezero/terrain/"
    "jezero_aoi_ctx_dem_20m.tif"
)


with rasterio.open(path) as ds:

    dem = ds.read(1).astype(np.float64)

    print("========== AOI INFO ==========")

    print("Size:", ds.width, "x", ds.height)

    print("Resolution:", ds.res)

    print("CRS:", ds.crs)

    print("Bounds:", ds.bounds)

    print("NoData:", ds.nodata)

    print("Min elevation:", np.nanmin(
        np.where(dem == ds.nodata, np.nan, dem)
    ))

    print("Max elevation:", np.nanmax(
        np.where(dem == ds.nodata, np.nan, dem)
    ))