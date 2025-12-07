from pydantic import BaseModel


class GenerateRequest(BaseModel):
    """Request model for generating cat pictures."""

    gemini_api_key: str

    location: str
    forecast: dict
    cat_names: list[str]
    cat_descriptions: list[str]
    input_image_paths: list[str]
    art_styles: list[str]

    image_gen_aspect_ratio: str
    image_gen_resolution: str
    final_image_size: str

    display_profile: str | None
