"""
bootstrap_data.py

Run this once per environment (Colab notebook cell, Codespaces
terminal, or your own machine) to pull all project data from Kaggle
into the exact paths the backend and frontend expect.

Usage:
    python scripts/bootstrap_data.py                 # fetch everything
    python scripts/bootstrap_data.py --only tiles     # fetch one raw entry
    python scripts/bootstrap_data.py --skip tiles     # fetch all but one
    python scripts/bootstrap_data.py --raw-only       # skip the bulk/processed download

Requirements:
    pip install kagglehub pyyaml

Kaggle credentials (same on every environment):
    - Colab:      store KAGGLE_USERNAME / KAGGLE_KEY as Colab secrets,
                  or upload kaggle.json to ~/.kaggle/kaggle.json
    - Codespaces: add KAGGLE_USERNAME / KAGGLE_KEY as Codespaces secrets
    - Local:      ~/.kaggle/kaggle.json (standard Kaggle CLI setup)

This script does NOT regenerate tiles / DEM crops / CRISM alignment.
That heavy pipeline is run once by whoever owns it, then re-uploaded
to the "processed" Kaggle dataset (see scripts/publish_processed_data.py).
Everyone else just downloads.
"""

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

import yaml

try:
    import kagglehub
except ImportError:
    print("Missing dependency. Run: pip install kagglehub pyyaml")
    sys.exit(1)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifest.yaml"


def load_manifest():
    with open(MANIFEST_PATH, "r") as f:
        return yaml.safe_load(f)


def fetch_file(dataset_slug, key, entry):
    target = PROJECT_ROOT / entry["target"]

    if target.exists():
        print(f"  - {key}: already present, skipping ({target})")
        return

    print(f"  - {key}: downloading '{entry['source']}' ...")
    downloaded_path = Path(
        kagglehub.dataset_download(dataset_slug, path=entry["source"])
    )

    target.parent.mkdir(parents=True, exist_ok=True)

    if downloaded_path.suffix == ".zip":
        print(f"    unzipping into {target} ...")
        target.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(downloaded_path, "r") as zf:
            zf.extractall(target)
    elif downloaded_path.is_dir():
        shutil.copytree(downloaded_path, target)
    else:
        shutil.copy2(downloaded_path, target)

    print(f"    done -> {target}")


def fetch_bulk(key, entry):
    dataset_slug = entry["kaggle_dataset"]
    target = PROJECT_ROOT / entry["target"]

    if target.exists() and any(target.iterdir()):
        print(f"  - {key}: already present, skipping ({target})")
        return

    print(f"  - {key}: downloading whole dataset '{dataset_slug}' ...")
    cache_path = Path(kagglehub.dataset_download(dataset_slug))

    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists():
        for item in cache_path.iterdir():
            dest = target / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)
    else:
        shutil.copytree(cache_path, target)

    print(f"    done -> {target}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="Comma-separated raw manifest keys to fetch")
    parser.add_argument("--skip", help="Comma-separated raw manifest keys to skip")
    parser.add_argument(
        "--raw-only", action="store_true",
        help="Skip the bulk/processed dataset download",
    )
    args = parser.parse_args()

    manifest = load_manifest()
    dataset_slug = manifest["kaggle_dataset"]
    files = manifest.get("files", {})
    bulk = manifest.get("bulk", {})

    only = set(args.only.split(",")) if args.only else None
    skip = set(args.skip.split(",")) if args.skip else set()

    print(f"Raw dataset: {dataset_slug}")
    for key, entry in files.items():
        if only is not None and key not in only:
            continue
        if key in skip:
            continue
        fetch_file(dataset_slug, key, entry)

    if not args.raw_only:
        print("\nProcessed (bulk) data:")
        for key, entry in bulk.items():
            fetch_bulk(key, entry)
    else:
        print("\n--raw-only set: skipping bulk/processed data.")

    print("\nDone. Data is in place under data/raw/ and data/processed/.")


if __name__ == "__main__":
    main()
