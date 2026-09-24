from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api.route import router as navigation_router


# ============================================================
# FastAPI Application Setup
# ============================================================

app = FastAPI(
    title="MarsWalk Intelligence",
    description="NASA-powered Mars exploration and route planning platform.",
    version="0.1.0"
)


# ============================================================
# Static Mars Map Tiles
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TILES_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "jezero"
    / "tiles"
    / "ctx_ortho"
)

app.mount(
    "/tiles/ctx",
    StaticFiles(directory=TILES_PATH),
    name="ctx-tiles",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# API Routers
# ============================================================

app.include_router(
    navigation_router,
    prefix="/api/v1",
    tags=["Navigation"]
)


# ============================================================
# Utility Endpoints
# ============================================================

@app.get("/")
def root():
    return {
        "project": "MarsWalk Intelligence",
        "status": "online"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }