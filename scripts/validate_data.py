import re
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifest.yaml"

failures = []

EXPECTED_RASTERS = {
    "ctx_mosaic": {
        "width": 17766,
        "height": 20234,
        "count": 1,
        "dtype": "uint8",
        "resolution": 5.002,
        "nodata": None,
    },
    "ctx_dem": {
        "width": 4456,
        "height": 5067,
        "count": 1,
        "dtype": "float32",
        "resolution": 20.0,
        "nodata_required": True,
    },
}

CRISM_EXPECTED = {
    "samples": 847,
    "lines": 808,
    "bands": 3,
}


def fail(message):
    failures.append(message)
    print(f"  FAIL  {message}")


def ok(message):
    print(f"  ok    {message}")


def check_exists(key, path):
    if not path.exists():
        fail(f"{key}: missing ({path})")
        return False

    if path.is_file() and path.stat().st_size == 0:
        fail(f"{key}: empty file")
        return False

    if path.is_file():
        ok(f"{key}: {path.stat().st_size:,} bytes")

    return True


def check_raster(key, path):
    import rasterio

    expected = EXPECTED_RASTERS.get(key)

    try:
        with rasterio.open(path) as ds:
            if not ds.crs:
                fail(f"{key}: missing CRS")
            else:
                ok(f"{key}: CRS present")

            if expected:
                for attr in ("width", "height", "count"):
                    actual = getattr(ds, attr)
                    if actual != expected[attr]:
                        fail(f"{key}: {attr}={actual}, expected {expected[attr]}")

                if ds.dtypes[0] != expected["dtype"]:
                    fail(f"{key}: dtype={ds.dtypes[0]}")

                resolution = abs(ds.transform.a)

                if abs(resolution - expected["resolution"]) > 0.01:
                    fail(f"{key}: resolution={resolution}")

                if expected.get("nodata_required") and ds.nodata is None:
                    fail(f"{key}: expected NoData value")

                if "nodata" in expected and ds.nodata != expected["nodata"]:
                    fail(f"{key}: unexpected NoData={ds.nodata}")

            # Read by windows to avoid loading huge rasters into memory.
            valid_count = 0
            min_value = float("inf")
            max_value = float("-inf")

            for _, window in ds.block_windows(1):
                arr = ds.read(1, window=window, masked=True)

                if arr.count():
                    valid_count += int(arr.count())
                    min_value = min(min_value, float(arr.min()))
                    max_value = max(max_value, float(arr.max()))

            if valid_count == 0:
                fail(f"{key}: no valid pixels")
            else:
                ok(f"{key}: {valid_count:,} valid pixels")
                ok(f"{key}: range [{min_value:.4f}, {max_value:.4f}]")

    except Exception as exc:
        fail(f"{key}: raster validation error: {exc}")


def parse_hdr(path):
    text = path.read_text(errors="replace")
    result = {}

    for key in ("samples", "lines", "bands", "data type",
                "byte order", "interleave"):
        match = re.search(
            rf"^\s*{re.escape(key)}\s*=\s*(\S+)",
            text, re.I | re.M
        )
        if match:
            result[key] = match.group(1).lower()

    return result


def check_crism(files):
    img = files.get("crism_image")
    hdr = files.get("crism_header")

    if not img or not hdr or not img.exists() or not hdr.exists():
        fail("CRISM: required image/header missing")
        return

    metadata = parse_hdr(hdr)

    for key, expected in CRISM_EXPECTED.items():
        try:
            actual = int(metadata.get(key, -1))
        except ValueError:
            actual = -1

        if actual != expected:
            fail(f"CRISM {key}: {actual}, expected {expected}")

    if metadata.get("data type") != "1":
        fail("CRISM: expected ENVI data type 1 (uint8)")

    expected_size = (
        CRISM_EXPECTED["samples"]
        * CRISM_EXPECTED["lines"]
        * CRISM_EXPECTED["bands"]
    )

    if img.stat().st_size != expected_size:
        fail(f"CRISM image size mismatch: {img.stat().st_size}")
    else:
        ok(f"CRISM image size: {expected_size:,} bytes")


def main():
    print("=" * 55)
    print("MARSWALK DATA VALIDATION")
    print("=" * 55)

    try:
        manifest = yaml.safe_load(MANIFEST_PATH.read_text())
    except Exception as exc:
        print(f"Cannot read manifest: {exc}")
        sys.exit(1)

    files = {}

    print("\n[1] RAW DATA")

    for key, entry in manifest.get("files", {}).items():
        path = PROJECT_ROOT / entry["target"]
        files[key] = path

        if check_exists(key, path):
            if path.suffix.lower() in (".tif", ".tiff"):
                check_raster(key, path)

    print("\n[2] CRISM CONSISTENCY")
    check_crism(files)

    print("\n[3] PROCESSED DATA")

    for key, entry in manifest.get("bulk", {}).items():
        path = PROJECT_ROOT / entry["target"]

        if path.is_dir() and any(path.iterdir()):
            ok(f"{key}: directory exists and is not empty")
        else:
            fail(f"{key}: missing or empty directory ({path})")

    print("\n" + "=" * 55)

    if failures:
        print(f"VALIDATION FAILED: {len(failures)} issue(s)")
        sys.exit(1)

    print("ALL CHECKS PASSED")
    print("=" * 55)


if __name__ == "__main__":
    main()
