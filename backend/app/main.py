from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.route import router as navigation_router


# ============================================================
# FastAPI Application Setup
# ============================================================

app = FastAPI(
    title="MarsWalk Intelligence",
    description="NASA-powered Mars exploration and route planning platform.",
    version="0.1.0"
)

# Enable CORS for frontend integration
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

# Include the navigation router
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
    # Return project basic information
    return {
        "project": "MarsWalk Intelligence",
        "status": "online"
    }


@app.get("/health")
def health():
    # Return server health status
    return {
        "status": "healthy"
    }

