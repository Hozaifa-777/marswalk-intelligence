# MarsWalk Intelligence — Backend ↔ Frontend Integration Guide

This is the single reference for anyone working on the frontend: what
the backend actually provides, how the Mars coordinate system works,
what's already wired up, and what's still open. Written from what has
been directly confirmed working — not assumptions.

---

## 1. Running the stack

See `docs/SETUP.md` for full environment setup (local / Codespaces /
Colab). Quick reference:

```bash
# data (once per environment)
python scripts/bootstrap_data.py

# backend
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# frontend
cd frontend && npm run dev -- --host 0.0.0.0 --port 5173
```

`vite.config.mjs` proxies both `/tiles` and `/api` to
`http://localhost:8000`, so the frontend calls relative paths
(`/tiles/...`, `/api/v1/...`) and never needs to know the backend's
actual host — this matters especially behind ngrok/Codespaces
forwarding, where the browser only ever talks to the Vite dev server.

---

## 2. Backend API Contract (verified)

The API contract below was retrieved directly from the running FastAPI application's "/openapi.json".

Available Endpoints

Method| Endpoint| Purpose
GET| "/health"| Backend health check
GET| "/"| Root endpoint
POST| "/api/v1/navigate"| A* route calculation
POST| "/api/v1/mission/consumables"| Mission oxygen and duration estimation
GET| "/api/v1/science/targets"| Science target GeoJSON

2.1 Navigation API

"POST /api/v1/navigate"

Request:

{
  "start": [4350000, 1090000],
  "goal": [4355000, 1095000],
  "mode": "balanced"
}

- "start": Required Mars coordinates "[x, y]".
- "goal": Required Mars coordinates "[x, y]".
- "mode": Optional; "fastest", "balanced", or "conservative".
- Default mode: "balanced".

Response: "GeoJSONResponse" (FeatureCollection).

Each feature contains:

- "geometry": LineString with Mars coordinate pairs.
- "properties.mode"
- "properties.distance_km"
- "properties.raw_terrain_cost"
- "properties.average_raw_terrain_cost"
- "properties.optimization_cost"
- "properties.average_optimization_cost"

2.2 Mission Consumables API

"POST /api/v1/mission/consumables"

Required request fields:

- "distance_km": Total route distance in kilometers, greater than zero.
- "average_raw_terrain_cost": Average terrain cost multiplier.

Optional fields:

- "average_slope_percent": Defaults to 0.0.
- "payload_kg": Defaults to 0.0.
- "base_walking_speed_ms": Defaults to 0.35.
- "suit_capacity_hours": Defaults to 8.5.

Response fields:

- "estimated_duration_hours"
- "estimated_oxygen_liters"
- "oxygen_percent_of_suit_capacity"
- "average_metabolic_rate_kcal_hr"
- "slope_penalty_kcal_hr"
- "payload_penalty_kcal_hr"
- "safety_margin_hours"
- "assumptions"

The assumptions object documents the parameters used by the estimation model.

2.3 Science Targets API

"GET /api/v1/science/targets"

Response: "ScienceTargetsResponse" (GeoJSON FeatureCollection).

Each feature contains:

- "geometry": Point with Mars coordinates.
- "properties.id"
- "properties.name"
- "properties.target_type"
- "properties.source"
- "properties.science_value"
- "properties.ranking_method"
- "properties.evidence"

Each evidence entry includes:

- "parameter"
- "value_dn"
- "threshold_dn"
- "relative_percentile"
- "passed_threshold"

2.4 Validation

FastAPI returns HTTP 422 for request validation errors.

To inspect the current contract:

python -c "import json,urllib.request; print(json.dumps(json.load(urllib.request.urlopen('http://localhost:8000/openapi.json')),indent=2))"

The running OpenAPI specification is the source of truth for request and response schemas. Do not guess field names or response structures.

---

## 3. Coordinate system — read this before touching the map

The whole project uses a **custom Mars CRS**, not Web Mercator /
EPSG:3857. Getting this wrong silently breaks alignment between
layers.

- **Projection:** Mars Equirectangular (Mars_2000_Sphere), standard
  parallel `18.4663°`, central meridian `0°`, units in meters.
- **CTX mosaic native pixel size:** ~5.002 m/px.
- **Tile scheme:** XYZ (not TMS), 256×256 tiles, native zoom = 7.
- **Full CTX bounds** (Mars projected meters):
  `xmin=4329192.108, ymin=1042131.635, xmax=4418059.789, ymax=1143347.424`
- **Operational AOI** (the 10×10 km sector routing/science work
  happens in — see `data/processed/jezero/map_metadata.json`):
  x: `4,350,000–4,360,000`, y: `1,090,000–1,100,000`.

**Critical convention:** under `MarsCRS` (`frontend/src/utils/marsCRS.js`),
Leaflet's `[lat, lng]` maps to `[Mars Y, Mars X]`. Every marker,
bounds, and polyline in this project follows that — e.g. a point
`(x, y)` in Mars meters becomes Leaflet `[y, x]`, not `[x, y]`. Get
this backwards and everything renders in the wrong place with no
error.

---

## 4. Frontend structure (as it exists now)

```
frontend/src/
├── App.jsx                        — layout + layers state (ctx, aoi)
├── App.css
├── components/
│   ├── HUD/HUD.jsx                — top bar, mission status
│   ├── ControlPanel/ControlPanel.jsx — layer toggle sidebar
│   ├── MarsMap/
│   │   ├── MarsMap.jsx            — the Leaflet map itself
│   │   └── AOILayer.jsx           — dashed AOI boundary rectangle
│   ├── POIPanel/                  — empty, reserved for science targets (Phase 5/7)
│   └── RouteComparison/           — empty, reserved for comparing route modes
├── utils/
│   ├── marsCRS.js                 — the custom Leaflet CRS (see §3)
│   └── mapConfig.js               — MARS_MAP.bounds (the AOI box)
```

Layer visibility is plain React state in `App.jsx` (`{ctx, aoi}`),
passed down to `MarsMap` and `ControlPanel`. Anything added to
`ControlPanel` (DEM, Slope, CRISM, Science Targets — currently
disabled checkboxes) should follow the same pattern: add a key to
that state object, pass it to `MarsMap`, conditionally render the
corresponding layer.

---

## 5. Known map behavior — not bugs

- **Empty space on the sides at high zoom-out, or at min zoom:** the
  CTX raster's aspect ratio doesn't match a landscape screen — this
  is expected, not broken. `zoomSnap={0.25}` + `map.setMinZoom(map.getZoom())`
  after `fitBounds` (already in `MarsMap.jsx`) prevents zooming out
  past "whole image visible."
- **Dark region on part of the map at wide zoom-out:** unresolved
  whether this is (a) genuinely outside the CTX mosaic's real
  coverage, or (b) leftover un-transparent nodata pixels from tile
  generation. Not investigated further — deprioritized in favor of
  Start/Goal work. To test: temporarily set the map's `background` to
  a bright non-black color and see if the region changes color (real
  gap) or stays dark (still-unfixed nodata).

---

## 6. Data (see `docs/SETUP.md` for full detail)

- Raw source rasters + CRISM: Kaggle dataset `hozaifa123/marswalk-data`
  (individual named files).
- Processed (tiles, AOI-cropped DEM, aligned CRISM signal): Kaggle
  dataset `hozaifa123/marswalk-processed-jezero`, downloaded as one
  whole tree via `scripts/bootstrap_data.py` (not per-file — the
  tiles folder alone is 7,490 files).
- Nobody besides the pipeline owner should ever need to run GDAL /
  `gdal2tiles.py` / `crop_aoi.py` / `align_crism_to_dem.py` directly.

---

## 7. Open items (in priority order)

1. **Confirm `/api/v1/navigate` schema** (§2) — blocks Start/Goal wiring.
2. **Start/Goal selection** — click-to-place on the map, route mode
   selector, "Calculate Route" button, draw the returned route
   (`RouteLayer.jsx`, in progress).
3. **Science targets on the map** — `/api/v1/science/targets` already
   returns real GeoJSON (placeholder coordinates); needs a map layer
   + `POIPanel` UI.
4. **Terrain/Slope/CRISM visual layers** — data exists
   (`data/processed/jezero/terrain/`, `.../science/crism/`), no
   frontend layer yet.
5. **RouteComparison** — once multiple route modes can be requested,
   compare them side by side (distance/cost/risk).
