from pathlib import Path

import numpy as np
import rasterio


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CRISM_IMG = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "jezero"
    / "science"
    / "crism"
    / "frt000047a3_07_brcarj_mtr3.img"
)

DEM_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "jezero"
    / "terrain"
    / "jezero_aoi_ctx_dem_20m.tif"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "jezero"
    / "science"
    / "crism"
    / "frt000047a3_carbonate_browse_signal_20m.tif"
)


# --------------------------------------------------
# CRISM browse image metadata
# --------------------------------------------------

CRISM_LINES = 808
CRISM_SAMPLES = 847
CRISM_BANDS = 3

CRISM_PIXEL_SIZE = 18.0

CRISM_UPPER_LEFT_X = 4428386.8
CRISM_UPPER_LEFT_Y = 1107292.6

CRISM_REFERENCE_LATITUDE = 15.0
CRISM_RADIUS = 3394839.8

IGNORE_VALUE = 255


# --------------------------------------------------
# DEM projection metadata
# --------------------------------------------------

DEM_RADIUS = 3396190.0
DEM_REFERENCE_LATITUDE = 18.4663


def crism_pixels_to_latlon(rows, cols):
    """
    Convert CRISM pixel centers to Mars latitude/longitude.
    """

    x = (
        CRISM_UPPER_LEFT_X
        + (cols + 0.5) * CRISM_PIXEL_SIZE
    )

    y = (
        CRISM_UPPER_LEFT_Y
        - (rows + 0.5) * CRISM_PIXEL_SIZE
    )

    lat = np.degrees(
        y / CRISM_RADIUS
    )

    lon = np.degrees(
        x
        / (
            CRISM_RADIUS
            * np.cos(
                np.radians(CRISM_REFERENCE_LATITUDE)
            )
        )
    )

    return lat, lon


def mars_latlon_to_dem_xy(lat, lon):
    """
    Convert Mars latitude/longitude into
    the projected coordinate system used
    by the Jezero DEM.
    """

    dem_x = (
        DEM_RADIUS
        * np.radians(lon)
        * np.cos(
            np.radians(DEM_REFERENCE_LATITUDE)
        )
    )

    dem_y = (
        DEM_RADIUS
        * np.radians(lat)
    )

    return dem_x, dem_y


def main():

    print("Loading CRISM browse image...")

    raw = np.fromfile(
        CRISM_IMG,
        dtype=np.uint8,
    )

    expected_size = (
        CRISM_BANDS
        * CRISM_LINES
        * CRISM_SAMPLES
    )

    if raw.size != expected_size:
        raise ValueError(
            f"Unexpected CRISM size: "
            f"{raw.size} != {expected_size}"
        )

    crism = raw.reshape(
        CRISM_BANDS,
        CRISM_LINES,
        CRISM_SAMPLES,
    )

    # Band 1 = D2300
    signal = crism[0].astype(
        np.float32
    )

    print(
        f"CRISM shape: {signal.shape}"
    )

    print("Loading DEM...")

    with rasterio.open(DEM_PATH) as dem:

        dem_data = dem.read(1)

        dem_transform = dem.transform
        dem_profile = dem.profile.copy()

        dem_height, dem_width = dem_data.shape

        print(
            f"DEM shape: "
            f"{dem_height} x {dem_width}"
        )

        # --------------------------------------------------
        # Create output science raster
        # --------------------------------------------------

        science_grid = np.zeros(
            (dem_height, dem_width),
            dtype=np.float32,
        )

        counts = np.zeros(
            (dem_height, dem_width),
            dtype=np.uint16,
        )

        # --------------------------------------------------
        # Create coordinates for every CRISM pixel
        # --------------------------------------------------

        rows, cols = np.indices(
            (CRISM_LINES, CRISM_SAMPLES)
        )

        rows = rows.ravel()
        cols = cols.ravel()

        values = signal.ravel()

        # Remove invalid pixels
        valid = values != IGNORE_VALUE

        rows = rows[valid]
        cols = cols[valid]
        values = values[valid]

        print(
            f"Valid CRISM pixels: "
            f"{values.size}"
        )

        # --------------------------------------------------
        # CRISM pixel
        #      ↓
        # Mars latitude / longitude
        # --------------------------------------------------

        lat, lon = crism_pixels_to_latlon(
            rows,
            cols,
        )

        # --------------------------------------------------
        # Mars latitude / longitude
        #      ↓
        # DEM projected coordinates
        # --------------------------------------------------

        x, y = mars_latlon_to_dem_xy(
            lat,
            lon,
        )

        # --------------------------------------------------
        # DEM coordinates
        #      ↓
        # DEM row / column
        # --------------------------------------------------

        dem_rows, dem_cols = rasterio.transform.rowcol(
            dem_transform,
            x,
            y,
        )

        dem_rows = np.asarray(
            dem_rows
        )

        dem_cols = np.asarray(
            dem_cols
        )

        # --------------------------------------------------
        # Keep only pixels inside DEM
        # --------------------------------------------------

        inside = (
            (dem_rows >= 0)
            & (dem_rows < dem_height)
            & (dem_cols >= 0)
            & (dem_cols < dem_width)
        )

        dem_rows = dem_rows[inside]
        dem_cols = dem_cols[inside]
        values = values[inside]

        print(
            "CRISM pixels mapped inside DEM: "
            f"{values.size}"
        )

        # --------------------------------------------------
        # Multiple CRISM pixels can map to one
        # 20 m DEM cell.
        #
        # For MVP:
        # keep the maximum observed signal.
        # --------------------------------------------------

        np.add.at(
            counts,
            (dem_rows, dem_cols),
            1,
        )

        np.maximum.at(
            science_grid,
            (dem_rows, dem_cols),
            values,
        )

        # Cells without CRISM observations
        # become NoData.
        science_grid[
            counts == 0
        ] = np.nan

        # --------------------------------------------------
        # Save GeoTIFF
        # --------------------------------------------------

        output_profile = dem_profile.copy()

        output_profile.update(
            dtype="float32",
            count=1,
            nodata=np.nan,
            compress="deflate",
        )

        OUTPUT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with rasterio.open(
            OUTPUT_PATH,
            "w",
            **output_profile,
        ) as dst:

            dst.write(
                science_grid,
                1,
            )

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    populated = np.isfinite(
        science_grid
    )

    print()
    print("Alignment complete.")
    print(
        f"Output: {OUTPUT_PATH}"
    )

    print(
        f"DEM cells: "
        f"{science_grid.size}"
    )

    print(
        f"Cells with CRISM signal: "
        f"{populated.sum()}"
    )

    print(
        f"Coverage: "
        f"{100 * populated.mean():.2f}%"
    )

    if populated.any():

        print(
            f"Signal min: "
            f"{np.nanmin(science_grid):.2f}"
        )

        print(
            f"Signal max: "
            f"{np.nanmax(science_grid):.2f}"
        )

        print(
            f"Signal mean: "
            f"{np.nanmean(science_grid):.2f}"
        )


if __name__ == "__main__":
    main()