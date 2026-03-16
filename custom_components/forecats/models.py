from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel


class Pet(BaseModel):
    name: str
    type: str
    description: str


class GenerateRequest(BaseModel):
    """Request model for generating pet pictures."""

    provider: str = "gemini"
    gemini_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    openrouter_text_model: Optional[str] = None
    openrouter_image_model: Optional[str] = None

    location: str
    forecast: Dict
    temperature_unit: str
    pets: List[Pet]
    input_image_paths: List[str]
    art_styles: List[str]

    image_gen_aspect_ratio: str
    image_gen_resolution: str
    final_image_size: str

    display_profile: Optional[str]
