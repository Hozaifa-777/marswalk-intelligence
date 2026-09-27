"""
publish_processed_data.py

Only the person who re-ran the heavy geospatial pipeline
(crop_aoi.py -> align_crism_to_dem.py -> tile generation) runs this.
It pushes data/processed/ as a new version of the Kaggle
"processed" dataset, so teammates' next `bootstrap_data.py` run
picks up the update automatically.

Usage:
    python scripts/publish_processed_data.py -m "Regenerated z7 tiles with alpha padding"

Requirements:
    pip install kaggle
    ~/.kaggle/kaggle.json configured (same credentials as bootstrap_data.py)
"""

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifest.yaml"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--message", required=True, help="Version change message")
    args = parser.parse_args()

    with open(MANIFEST_PATH, "r") as f:
        manifest = yaml.safe_load(f)

    dataset_slug = manifest.get("processed_kaggle_dataset", manifest.get("kaggle_dataset"))

    print(f"Publishing {PROCESSED_DIR} -> {dataset_slug}")

    result = subprocess.run(
        [
            "kaggle", "datasets", "version",
            "-p", str(PROCESSED_DIR),
            "-m", args.message,
            "-r", "zip",
        ],
        cwd=PROJECT_ROOT,
    )

    if result.returncode != 0:
        print("Publish failed. Make sure a dataset-metadata.json exists under "
              "data/processed/ (run `kaggle datasets init -p data/processed` once).")
        sys.exit(result.returncode)

    print(
        "\nPublished. Update data/manifest.yaml with the real file paths and tell "
        "the team to re-run bootstrap_data.py."
    )


if __name__ == "__main__":
    main()
