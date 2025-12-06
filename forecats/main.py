"""FastAPI for serving cat pictures."""

import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from forecats.forecats import generate_cat_pic
from forecats.logging import LOG_FILE, setup_logging

setup_logging()
logger = logging.getLogger("forecats")


class GenerateRequest(BaseModel):
    """Request model for generating cat pictures."""

    location: str
    forecast: dict
    cat_names: list[str]
    cat_descriptions: list[str]
    input_image_urls: list[str]
    art_styles: list[str]

    image_gen_aspect_ratio: str
    image_gen_resolution: str
    final_aspect_ratio: str
    final_resolution: str


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
    """Generate and return a cat picture based on the weather forecast."""
    data = request.model_dump()
    try:
        image = generate_cat_pic(data)
        filepath = Path("./static/images/forecats.png")
        filepath.parent.mkdir(parents=True, exist_ok=True)
        image.save(filepath)

        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        url = f"{base_url}/static/images/{filepath.name}"

    except Exception as e:
        logger.exception(f"Error generating cat picture: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate cat picture: {e!s}",
        ) from e

    return {"download_url": url}
