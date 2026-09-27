# MarsWalk Intelligence — Team Setup Guide

Follow this once per environment (your laptop, a fresh Codespace, or a
Colab notebook). Everything here is copy-paste; no decisions needed.

---

## 0. Prerequisites (one-time, per person)

You need a Kaggle account with API access, regardless of which
environment you run the project on.

1. Create a Kaggle account if you don't have one.
2. Go to **kaggle.com → Account → API → Create New Token**.
   This downloads a `kaggle.json` file.
3. Keep that file somewhere safe — you'll upload it below.

---

## 1. Get the code

```bash
git clone https://github.com/Hozaifa-777/marswalk-intelligence.git
cd marswalk-intelligence
```

---

## 2. Get the data

### 2.1 Kaggle credentials (do this first, every environment)

**Local machine / GitHub Codespaces (terminal):**
```bash
mkdir -p ~/.kaggle
mv /path/to/kaggle.json ~/.kaggle/kaggle.json
chmod 600 ~/.kaggle/kaggle.json
```

**Google Colab (notebook cell):**
```python
from google.colab import files
uploaded = files.upload()   # pick kaggle.json when prompted

!mkdir -p ~/.kaggle
!mv kaggle.json ~/.kaggle/
!chmod 600 ~/.kaggle/kaggle.json
```

### 2.2 Install the data dependencies

```bash
pip install -q kagglehub pyyaml
```

### 2.3 Pull all project data

```bash
python scripts/bootstrap_data.py
```

This fetches everything from the team's shared Kaggle dataset
(`hozaifa123/marswalk-data`) into `data/raw/` and `data/processed/`,
matching exactly what `data/manifest.yaml` describes. It skips
anything already present, so it's safe to re-run any time.

If a specific file is missing or renamed on Kaggle, this step will
fail with a clear "source not found" message — check
`data/manifest.yaml` against the real file list:
```bash
kaggle datasets files hozaifa123/marswalk-data
```

**You should never need to run GDAL, `gdal2tiles.py`, or any of the
`scripts/crop_aoi.py` / `scripts/align_crism_to_dem.py` pipeline
yourself.** That heavy processing is done once by whoever owns the
geospatial pipeline, then published to Kaggle. `bootstrap_data.py` is
the only command anyone else needs.

---

## 3. Run the backend

```bash
cd backend
pip install -q -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify it's up (new terminal, or after backgrounding it):
```bash
curl http://localhost:8000/health
# expect: {"status":"healthy"}
```

---

## 4. Run the frontend

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

`vite.config.mjs` already proxies `/tiles` and `/api` to
`localhost:8000`, so the frontend talks to the backend automatically —
no extra config needed.

---

## 5. Open the app (depends on your environment)

- **Local machine:** open `http://localhost:5173` directly.
- **GitHub Codespaces:** open the **Ports** tab, find port 5173, click
  the globe icon to open the forwarded URL. Set visibility to
  "Public" if a teammate needs the link too.
- **Google Colab:** Colab has no direct URL to a running port, so
  tunnel it with ngrok:

  ```python
  !pip install -q pyngrok
  from pyngrok import ngrok

  ngrok.set_auth_token("YOUR_NGROK_AUTHTOKEN")  # from dashboard.ngrok.com/get-started/your-authtoken
  public_url = ngrok.connect(5173)
  print(public_url)
  ```
  Open the printed `https://xxxx.ngrok-free.app` link. (Free ngrok
  tokens are personal — each teammate should use their own, not share
  one in chat/commits.)

---

## 6. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ECONNREFUSED` on `/tiles/...` in the Vite log | Backend isn't running | Go back to step 3 |
| `Blocked request. This host ... is not allowed` | Vite's host check (only hits behind ngrok/Codespaces) | Already fixed in `vite.config.mjs` (`allowedHosts: true`) |
| `Failed to resolve import "./components/X/X"` | A component file is missing | Should not happen once the repo is up to date — `git pull` |
| `rasterio.errors.RasterioIOError: ... No such file` | Data not fetched, or `data/manifest.yaml` paths don't match what a script expects | Re-run `bootstrap_data.py`; check the exact path in the error against the manifest |
| Map loads but is entirely black | Backend not serving tiles, or CTX layer unchecked in the sidebar | Check `curl http://localhost:8000/tiles/ctx/0/0/0.png` returns `200` |

---

## 7. If you're the one regenerating processed data (tiles/DEM/CRISM)

Only do this if you've changed the source rasters or the processing
scripts. Everyone else just runs `bootstrap_data.py`.

```bash
python scripts/crop_aoi.py
python scripts/align_crism_to_dem.py
gdal2tiles.py -p raster --xyz -r bilinear \
  data/raw/jezero/ctx_ortho/M20_JezeroCrater_CTXortho_mosaic_5m.tif \
  data/processed/jezero/tiles/ctx_ortho

python scripts/publish_processed_data.py -m "describe what changed"
```

Then update `data/manifest.yaml` with the real file paths from:
```bash
kaggle datasets files hozaifa123/marswalk-processed-jezero
```

and tell the team to re-run `bootstrap_data.py`.
