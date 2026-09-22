from fastapi import FastAPI

app = FastAPI(
    title="MarsWalk Intelligence",
    description="NASA-powered Mars exploration and route planning platform.",
    version="0.1.0"
)


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
    