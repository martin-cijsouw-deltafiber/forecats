"""FastAPI for serving cat pictures."""

import logging
import os

from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles

from forecats.forecats import generate_cat_pic
from forecats.logging import LOG_FILE, setup_logging
from forecats.models import GenerateRequest

setup_logging()
logger = logging.getLogger("forecats")

app = FastAPI(
    title="ForeCats API",
    description="Generate weather forecast cat pictures",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/logs")
def get_logs() -> dict:
    """Return recent log files."""
    if not LOG_FILE.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log file not found")

    with LOG_FILE.open("r") as f:
        log_content = f.read()

    return {"logs": log_content}


@app.get("/")
def read_root() -> dict:
    """Root endpoint with API information."""
    return {
        "name": "ForeCats API",
        "version": "1.0.0",
        "endpoints": {
            "POST /generate": "Generate and return a cat picture",
            "GET /logs": "Get log file",
        },
    }


@app.post("/generate")
def generate(request: GenerateRequest) -> dict:
    """Generate cat pic in static and return download URL."""
    try:
        filename = generate_cat_pic(request)
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        url = f"{base_url}/static/images/{filename}"

    except Exception as e:
        logger.exception(f"Error generating cat picture: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate cat picture: {e!s}",
        ) from e

    print(url)  # TODO remove
    return {"download_url": url}
