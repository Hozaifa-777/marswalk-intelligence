MarsWalk Intelligence — Team Setup Guide

This guide explains how to set up and run MarsWalk Intelligence in a fresh environment.

Supported environments:

- GitHub Codespaces
- Local Linux / macOS / Windows (WSL)
- Google Colab (backend/frontend with tunneling)

The project uses shared datasets hosted on Kaggle. No manual geospatial preprocessing is required for normal team members.

---

0. Prerequisites

Install or prepare:

- Python 3.10+
- Node.js and npm
- Git
- A Kaggle account with access to the team's datasets

Shared datasets:

Dataset| Purpose
"hozaifa123/marswalk-data"| Raw CTX and CRISM data
"hozaifa123/marswalk-processed-jezero"| Processed DEM, CRISM products, and map tiles

Repository:

"https://github.com/Hozaifa-777/marswalk-intelligence"

---

1. Clone the Repository

git clone https://github.com/Hozaifa-777/marswalk-intelligence.git
cd marswalk-intelligence

---

2. Configure Kaggle Authentication

Kaggle authentication is required to download private or restricted datasets.

Option A — API Token (Recommended)

Generate an API token from:

https://www.kaggle.com/settings

Set the environment variable:

export KAGGLE_API_TOKEN="YOUR_KAGGLE_API_TOKEN"

For GitHub Codespaces, add "KAGGLE_API_TOKEN" under repository or Codespace secrets.

For Google Colab, add "KAGGLE_API_TOKEN" to Colab Secrets and retrieve it using:

from google.colab import userdata
import os

os.environ["KAGGLE_API_TOKEN"] = userdata.get("KAGGLE_API_TOKEN")

Option B — Legacy kaggle.json

If using the legacy credentials file:

mkdir -p ~/.kaggle
mv /path/to/kaggle.json ~/.kaggle/kaggle.json
chmod 600 ~/.kaggle/kaggle.json

Do not commit credentials or share personal API tokens.

---

3. Download Project Data

Install the bootstrap dependencies:

python -m pip install kagglehub pyyaml

Download all required datasets:

python scripts/bootstrap_data.py

The bootstrap script downloads:

Raw data

- CTX orthomosaic
- CTX DEM
- CRISM label
- CRISM header
- CRISM image

Processed data

- Jezero AOI DEM
- CRISM science products
- CRISM overlays
- CTX map tiles
- Map metadata
- AOI boundary

The processed dataset contains a canonical nested "jezero/" directory. The bootstrap script selects that directory to preserve the expected project structure.

The resulting structure is:

data/
├── raw/
│   └── jezero/
│       ├── ctx_ortho/
│       ├── ctx_dem/
│       └── science/
│           └── crism/
│
└── processed/
    └── jezero/
        ├── science/
        │   └── crism/
        ├── terrain/
        └── tiles/
            └── ctx_ortho/

Optional Bootstrap Commands

Download only selected raw files:

python scripts/bootstrap_data.py --only ctx_mosaic,ctx_dem

Skip selected files:

python scripts/bootstrap_data.py --skip crism_image

Download raw data without processed data:

python scripts/bootstrap_data.py --raw-only

The script skips files and processed directories that already exist.

If a dataset file is missing or renamed, inspect its contents using:

kaggle datasets files hozaifa123/marswalk-data

---

4. Validate the Data

Before running the backend:

python scripts/validate_data.py

Expected final output:

ALL CHECKS PASSED

The validation script checks:

- Raw file existence and size
- CTX raster metadata and CRS
- DEM dimensions, resolution, and valid pixels
- CRISM header dimensions and image consistency
- Processed data directory availability

Do not proceed if validation fails.

---

5. Install and Run the Backend

Open a terminal:

cd backend
python -m pip install -r requirements.txt

Start FastAPI:

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

Verify the backend:

curl http://localhost:8000/health

Inspect the API documentation:

http://localhost:8000/docs

OpenAPI specification:

http://localhost:8000/openapi.json

Available API Endpoints

Method| Endpoint| Purpose
GET| "/health"| Health check
GET| "/"| Root endpoint
POST| "/api/v1/navigate"| A* route calculation
POST| "/api/v1/mission/consumables"| Mission consumables estimation
GET| "/api/v1/science/targets"| Science targets GeoJSON

The running OpenAPI specification is the source of truth for API request and response schemas.

---

6. Install and Run the Frontend

Open a second terminal from the repository root:

cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173

The frontend uses:

- React
- Vite
- Leaflet
- React Leaflet

The Vite development server proxies API and map tile requests to the backend.

Make sure both services are running:

Service| Port
FastAPI backend| 8000
Vite frontend| 5173

---

7. Open the Application

Local Machine

Open:

http://localhost:5173

GitHub Codespaces

1. Open the Codespaces Ports tab.
2. Locate port "5173".
3. Click the forwarded address.
4. Set port visibility appropriately if teammates need access.

Keep backend port "8000" available to the frontend through the Codespaces environment.

Google Colab

Colab does not directly expose localhost ports.

Use a tunneling service such as ngrok to expose the frontend.

Each teammate should use their own ngrok authentication token.

---

8. Troubleshooting

Problem| Possible cause| Solution
Kaggle authentication failure| Missing or invalid credentials| Configure "KAGGLE_API_TOKEN" or "kaggle.json"
Missing raw files| Bootstrap did not complete| Re-run "python scripts/bootstrap_data.py"
Validation failure| Incorrect or incomplete dataset| Inspect the failing path and compare it with "data/manifest.yaml"
"ModuleNotFoundError"| Missing Python dependency| Install "backend/requirements.txt"
"ECONNREFUSED"| Backend is not running| Start FastAPI on port 8000
Vite API requests fail| Backend unavailable or proxy misconfigured| Check backend and "vite.config.mjs"
Map appears black| Missing tiles or disabled CTX layer| Check the tile endpoint and sidebar layer settings
Port cannot be opened| Codespaces forwarding issue| Check the Ports tab and port visibility

---

9. Regenerating Processed Data (Maintainers Only)

Normal team members should NOT run this section.

Only run these scripts if the original source rasters or geospatial processing pipeline have changed.

python scripts/crop_aoi.py
python scripts/align_crism_to_dem.py

Regenerate CTX tiles if required:

gdal2tiles.py -p raster --xyz -r bilinear \
  data/raw/jezero/ctx_ortho/M20_JezeroCrater_CTXortho_mosaic_5m.tif \
  data/processed/jezero/tiles/ctx_ortho

Publish the updated processed dataset:

python scripts/publish_processed_data.py -m "Describe changes"

Verify the published dataset and update the shared Kaggle dataset version.

Notify the team to download the updated data.

---

10. Important Project Rules

- Never modify original files under "data/raw/".
- Do not manually regenerate processed data unless necessary.
- Do not commit large raster datasets or personal credentials.
- Keep the data manifest synchronized with actual dataset paths.
- Preserve the existing navigation architecture and A* implementation.
- Keep Science analysis separate from the Navigation Terrain Cost Function.
- Check API contracts through OpenAPI before changing frontend integration.

---

MarsWalk Intelligence — Team Setup Guide

For project-specific architecture and frontend/backend integration details, see:

"docs/pitch/FRONTEND_BACKEND_GUIDE.md"