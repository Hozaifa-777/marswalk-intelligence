
from functools import lru_cache
from pathlib import Path

import numpy as np
import rasterio

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from rasterio.io import MemoryFile
from rasterio.transform import array_bounds
from rasterio.warp import reproject, Resampling

from app.core.terrain.geotiff import load_terrain, PROJECT_ROOT


router = APIRouter(prefix="/api/v1/terrain", tags=["Terrain"])

CTX_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "jezero"
    / "ctx_ortho"
    / "M20_JezeroCrater_CTXortho_mosaic_5m.tif"
)


def _json_grid(values, valid_mask, decimals=2):
    """Convert numeric arrays to strict JSON rows."""
    rounded = np.round(values, decimals=decimals)

    return [
        [
            float(value) if valid else None
            for value, valid in zip(row, mask_row)
        ]
        for row, mask_row in zip(rounded, valid_mask)
    ]


def build_heightmap_payload(
    terrain: dict,
    max_dimension: int = 256,
) -> dict:

    dem = np.asarray(terrain["dem"], dtype=np.float64)
    slope = np.asarray(terrain["slope"], dtype=np.float64)
    transform = terrain["transform"]

    if dem.ndim != 2 or slope.shape != dem.shape:
        raise ValueError("DEM and slope must be matching 2D arrays.")

    rows, cols = dem.shape

    if rows == 0 or cols == 0:
        raise ValueError("Terrain raster is empty.")

    out_rows = min(max_dimension, rows)
    out_cols = min(max_dimension, cols)

    row_indices = np.unique(
        np.linspace(0, rows - 1, out_rows)
        .round()
        .astype(np.int32)
    )

    col_indices = np.unique(
        np.linspace(0, cols - 1, out_cols)
        .round()
        .astype(np.int32)
    )

    sampled_dem = dem[np.ix_(row_indices, col_indices)]
    sampled_slope = slope[np.ix_(row_indices, col_indices)]

    valid = (
        np.isfinite(sampled_dem)
        & np.isfinite(sampled_slope)
    )

    west, south, east, north = array_bounds(
        rows,
        cols,
        transform,
    )

    affine = list(transform)[:6]

    return {
        "crs": "Mars_2000_Sphere_Equirectangular",
        "coordinate_units": "meters",
        "elevation_units": "meters",
        "slope_units": "degrees",

        "width": int(len(col_indices)),
        "height": int(len(row_indices)),

        "source_width": int(cols),
        "source_height": int(rows),

        "resolution_m": [
            float(abs(transform.a)),
            float(abs(transform.e)),
        ],

        "bounds_m": {
            "xmin": float(west),
            "ymin": float(south),
            "xmax": float(east),
            "ymax": float(north),
        },

        "transform": [
            float(value) for value in affine
        ],

        "row_indices": row_indices.tolist(),
        "col_indices": col_indices.tolist(),

        "elevation_m": _json_grid(
            sampled_dem,
            valid,
        ),

        "slope_deg": _json_grid(
            sampled_slope,
            valid,
        ),

        "valid_mask": valid.tolist(),
    }


@lru_cache(maxsize=4)
def _cached_heightmap(max_dimension: int) -> dict:

    terrain = load_terrain()

    return build_heightmap_payload(
        terrain,
        max_dimension=max_dimension,
    )


@router.get("/heightmap")
def get_terrain_heightmap(
    max_dimension: int = Query(
        default=256,
        ge=32,
        le=512,
    ),
):

    try:
        return _cached_heightmap(max_dimension)

    except (
        FileNotFoundError,
        rasterio.errors.RasterioIOError,
    ):

        raise HTTPException(
            status_code=503,
            detail="Processed Jezero DEM is unavailable.",
        )

    except ValueError as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# CTX TEXTURE
# ============================================================

def build_ctx_texture():

    if not CTX_PATH.exists():
        raise FileNotFoundError(
            f"CTX image not found: {CTX_PATH}"
        )

    # Load the same processed DEM grid used by navigation.
    terrain = load_terrain()

    dem = terrain["dem"]
    target_transform = terrain["transform"]

    height, width = dem.shape

    # Read DEM CRS and metadata.
    dem_path = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "jezero"
        / "terrain"
        / "jezero_aoi_ctx_dem_20m.tif"
    )

    with rasterio.open(dem_path) as dem_src:
        target_crs = dem_src.crs
        target_bounds = dem_src.bounds

    with rasterio.open(CTX_PATH) as src:

        # Verify that CTX and DEM use compatible projected coordinates.
        if not src.crs.is_projected or not target_crs.is_projected:
            raise ValueError(
        "CTX and DEM must use projected coordinate systems."
    )

        source_units = src.crs.linear_units
        target_units = target_crs.linear_units

        if source_units != target_units:
            raise ValueError(
               f"CTX and DEM coordinate units differ: "
               f"{source_units} vs {target_units}"
    )

        if source_units != target_units:
            raise ValueError(
        "CTX and DEM coordinate units differ."
    )

        # Ensure the CTX image covers the entire DEM AOI.
        source_bounds = src.bounds

        tolerance = 1.0

        if (
            source_bounds.left > target_bounds.left + tolerance
            or source_bounds.right < target_bounds.right - tolerance
            or source_bounds.bottom > target_bounds.bottom + tolerance
            or source_bounds.top < target_bounds.top - tolerance
        ):
            raise ValueError(
                "CTX image does not fully cover the DEM AOI."
            )

        texture = np.zeros(
            (height, width),
            dtype=np.uint8,
        )

        reproject(
    source=rasterio.band(src, 1),
    destination=texture,
    src_transform=src.transform,
    src_crs=src.crs,
    dst_transform=target_transform,
    dst_crs=src.crs,
    resampling=Resampling.bilinear,
    init_dest_nodata=True,
        )

        # Check that the output actually contains image information.
    if not np.any(texture):
        raise ValueError("Generated CTX texture is empty.")

    # --------------------------------------------------------
    # MARS COLOR MAPPING
    # --------------------------------------------------------

    valid_pixels = np.isfinite(dem)

    if not np.any(valid_pixels):
        raise ValueError("DEM contains no valid pixels for texture mapping.")

    low, high = np.percentile(
        texture[valid_pixels],
        [2, 98],
    )

    if high <= low:
        raise ValueError("CTX texture has insufficient intensity variation.")

    normalized = np.clip(
        (texture.astype(np.float32) - low) / (high - low),
        0.0,
        1.0,
    )

    # Slight gamma adjustment to retain details in darker regions.
    normalized = np.power(normalized, 0.9)

    # Dark basalt -> reddish brown -> Martian dust -> pale terrain.
    stops = np.array(
        [0.0, 0.20, 0.45, 0.72, 1.0],
        dtype=np.float32,
    )

    palette = np.array(
        [
            [52, 39, 31],
            [105, 72, 51],
            [157, 111, 75],
            [195, 148, 104],
            [226, 190, 145],
        ],
        dtype=np.float32,
    )

    rgb = np.stack(
        [
            np.interp(normalized, stops, palette[:, channel])
            for channel in range(3)
        ],
        axis=0,
    )

    rgb = np.clip(rgb, 0, 255).astype(np.uint8)

    # Encode RGB PNG in memory.
    with MemoryFile() as memory_file:

        with memory_file.open(
            driver="PNG",
            width=width,
            height=height,
            count=3,
            dtype="uint8",
        ) as dst:

            dst.write(rgb)

        return memory_file.read()


@lru_cache(maxsize=1)
def _cached_ctx_texture():

    return build_ctx_texture()


@router.get("/texture")
def get_terrain_texture():

    try:
        png = _cached_ctx_texture()

        return Response(
            content=png,
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=3600",
                "X-Texture-Width": "500",
                "X-Texture-Height": "500",
                "X-Texture-Source": "CTX-Orthomosaic",
            },
        )

    except FileNotFoundError as error:

        raise HTTPException(
            status_code=503,
            detail=str(error),
        )

    except (
        rasterio.errors.RasterioIOError,
        ValueError,
    ) as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )
