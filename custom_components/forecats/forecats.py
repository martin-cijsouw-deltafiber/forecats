from __future__ import annotations

"""Generate pet pictures based on weather forecasts using Gemini or OpenRouter."""

import base64
import io
import json
import logging
import random
import textwrap
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from PIL import Image

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

try:
    from .image_processing import recolor_image, resize_image
    from .models import GenerateRequest
except ImportError:  # For local testing
    from image_processing import recolor_image, resize_image
    from models import GenerateRequest

_LOGGER = logging.getLogger(__name__)
_OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"


def generate_pet_pic(data: GenerateRequest, config_dir: str) -> tuple[str, str]:
    """Generate, crop, and dither a pet picture based on weather."""
    # Setup paths relative to HA config directory
    config_path = Path(config_dir)
    data_dir = config_path / "forecats_data"
    static_dir = Path(data.output_dir) if data.output_dir else config_path / "www" / "daily_forecats"

    data_dir.mkdir(parents=True, exist_ok=True)
    static_dir.mkdir(parents=True, exist_ok=True)

    prompt_history_filepath = data_dir / "forecats_prompt_history.txt"

    provider = (data.provider or "gemini").lower()
    if provider == "gemini" and not data.gemini_api_key:
        msg = "provider=gemini requires gemini_api_key"
        raise ValueError(msg)
    if provider == "openrouter":
        if not data.openrouter_api_key:
            msg = "provider=openrouter requires openrouter_api_key"
            raise ValueError(msg)
        if not data.openrouter_text_model:
            msg = "provider=openrouter requires openrouter_text_model"
            raise ValueError(msg)
        if not data.openrouter_image_model:
            msg = "provider=openrouter requires openrouter_image_model"
            raise ValueError(msg)
    if provider not in {"gemini", "openrouter"}:
        msg = f"Unsupported provider: {provider}"
        raise ValueError(msg)

    # Load resources
    prompt_history = load_prompt_history(prompt_history_filepath)
    images = load_images(data.input_image_paths)
    art_style = random.choice(data.art_styles)
    _LOGGER.info(f"Selected provider: {provider}")
    _LOGGER.info(f"Selected art style: {art_style}")

    if provider == "gemini" and genai is None:
        msg = "provider=gemini requires google-genai package to be installed"
        raise RuntimeError(msg)
    client = genai.Client(api_key=data.gemini_api_key) if provider == "gemini" else None

    # Generate activity description
    # TODO add an if-else to allow for date/activity overrides on particular days
    activity = generate_activity(provider, client, data, prompt_history)
    _LOGGER.info(f"Generated activity: {activity}")

    # Update prompt history
    prompt_history.append(activity)
    prompt_history = prompt_history[-20:]
    save_prompt_history(prompt_history_filepath, prompt_history)

    # Generate image
    _LOGGER.info(f"Generating image for: {activity}")
    image = generate_image(provider, client, data, activity, images, art_style)

    # Post-process image
    resized_image = resize_image(image.copy(), data.final_image_size)
    optimized_image = recolor_image(resized_image, data.display_profile)

    # Save images
    original_filepath = static_dir / "forecats_original.png"
    optimized_filepath = static_dir / "forecats_optimized.png"
    image.save(original_filepath)
    optimized_image.save(optimized_filepath)

    _LOGGER.info(f"Images saved to {static_dir}")

    return original_filepath, optimized_filepath


def load_prompt_history(filepath: Path) -> list[str]:
    """Load past prompts from file."""
    if filepath.exists():
        return filepath.read_text().splitlines()
    filepath.parent.mkdir(parents=True, exist_ok=True)
    return []


def save_prompt_history(filepath: Path, history: list[str]) -> None:
    """Save prompt history to file."""
    Path(filepath).write_text("\n".join(history))


def load_images(image_paths: list[str], max_size: int = 1024) -> dict[str, Image.Image]:
    """Load and resize images."""

    def resize(img_path: Path) -> Image.Image:
        img = Image.open(img_path)
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        return img

    paths = [Path(p) for p in image_paths]
    valid_paths = [p for p in paths if p.exists()]
    if not valid_paths:
        _LOGGER.warning(f"No valid image paths found from: {paths}")
    return {p.name: resize(p) for p in valid_paths}


def _build_activity_prompt(data: GenerateRequest, prompt_history: list[str]) -> str:
    pet_types = ", ".join(f"{pet.name}, {pet.type}" for pet in data.pets)
    return textwrap.dedent(
        f"""
        You are a prompt generator for static AI cartoon art generation model. Your task is to generate a seasonally appropriate activity for {len(data.pets)} pets to do based on the date and weather conditions provided, which will be used to draw a single picture.

        The pets are: {pet_types}.

        The date is {data.forecast.get("datetime", "")}.

        The weather forecast is for {data.location}.

        The forecast is:
        {data.forecast}

        The last 20 activities you generated were:
        {prompt_history}

        ************************************************

        Follow this prompt:

        Generate a fun activity for {len(data.pets)} pets to do together that fits the weather conditions and time of year.

        Heuristics:
        - You can anthropomorphize the pets to do human-like activities, or you can make them do more pet-like activities occasionally.
        - The activity can be either indoors or outdoors
        - The activity should be seasonally appropriate
        - Activities should be 30% set in locations in {data.location}, and 20% set in other specific locations with similar weather, and 50% set in generic locations.
        - The mix of indoor/outdoor should be seasonally appropriate. Summer is mostly outdoor, winter is 50/50 indoor/outdoor.
        - It can be a mundane activity (waiting for the bus, commuting, shopping, reading, etc.) or it can be exciting (playing in the snow, sports, going to a festival, playing tag, games, etc.).

        Rules:
        - You must come up with the following:
            - Activity: A short (<5 words) description of the activity
            - Foreground: A description of what the pets are doing, including any clothing or accessories they are wearing.
            - Background: A description of the background elements (e.g. buildings, landmarks, trees, furniture, etc.)
        - You don't have to describe the weather
        - Do not describe the general appearance of the pets, with the exception of clothing or accessories needed for the activity
        - The activity should involve all {len(data.pets)} pets
        - The activity must not be similar to any of the last 20 activities you generated.
        - Respond in a single line, no more than 100 words
        - Do not use newlines
        - Respond with "Activity: <activity>, Foreground: <foreground>, Background: <background>"
        """,
    )


def generate_activity(
    provider: str,
    client: Any,
    data: GenerateRequest,
    prompt_history: list[str],
) -> str:
    """Describe an activity for the pets based on the weather forecast and date."""
    activity_prompt = _build_activity_prompt(data, prompt_history)

    if provider == "gemini":
        if client is None:
            msg = "Gemini client is required for provider=gemini"
            raise RuntimeError(msg)
        activity_response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=activity_prompt,
        )
        if not activity_response.text:
            msg = "Gemini returned no activity."
            raise RuntimeError(msg)
        return activity_response.text

    response = _openrouter_post(
        "/chat/completions",
        {
            "model": data.openrouter_text_model,
            "messages": [{"role": "user", "content": activity_prompt}],
            "temperature": 0.8,
        },
        data.openrouter_api_key,
    )

    choices = response.get("choices", [])
    if not choices:
        msg = "OpenRouter returned no activity choices."
        raise RuntimeError(msg)
    content = choices[0].get("message", {}).get("content")
    text = _extract_openrouter_text(content)
    if not text:
        msg = "OpenRouter returned empty activity text."
        raise RuntimeError(msg)
    return text


def _build_image_generation_prompt(
    data: GenerateRequest,
    activity: str,
    input_images: dict[str, Image.Image],
    art_style: str,
    include_reference_images: bool,
) -> str:
    pets_information = "\n".join(
        f"- {pet.name}, {pet.type}, {pet.description}" for pet in data.pets
    )
    reference_instructions = ""
    if include_reference_images:
        reference_instructions = textwrap.dedent(
            f"""
            You will be given {len(input_images)} input images with these names (in this order):
            {", ".join(input_images.keys())}
            """
        )
    else:
        reference_instructions = (
            "No direct reference images are attached for this request. "
            "Use the pet descriptions as the source of truth for appearance."
        )

    return textwrap.dedent(
        f"""
        You are an AI artist creating daily weather illustrations featuring pets based on a weather forecast and an activity that will be given to you. Your task is to generate a vibrant and engaging illustration that captures the essence of the weather conditions and the pets' activity in a specific art style.

        The weather forecast is for {data.location} on {data.forecast.get("datetime", "")}:
        {data.forecast}

        You have {len(data.pets)} pets to illustrate, here are their name, type, and descriptions:
        {pets_information}

        The activity they are doing today is:
        {activity}

        The art style should be:
        {art_style}

        {reference_instructions}

        ***********************************************

        Create a vibrant and engaging illustration in the recommended style that captures the essence of the weather conditions and the pets' activity. Use colors and elements that reflect the forecasted weather, making the scene lively and appropriate for the time of year.

        Additionally, create a small box in the bottom left corner, in the style of the image. This box should contain:
        - A < three word description of the weather conditions
        - The daily high temperature (forecast field: temperature)
        - The daily low temperature (forecast field: templow)
        - Note that the temperatures are in {data.temperature_unit}

        Heuristics:
        - Try to capture the mood of the weather, season, and activity in the illustration (e.g., bright and sunny, cozy indoors during snow, etc.).
        - Try to capture the pets personalities, but it is okay if they change based on the weather and activity.
        - This is for a color e-ink screen. I will handle the dithering later, but try to avoid very fine details that may be lost in dithering.

        Rules:
        - Only generate a single image.
        - The final image will be cropped in postprocessing to {data.final_image_size}, so compose the image accordingly and DON'T place anything near the edges.
        - The weather is important, so include elements that clearly indicate the weather conditions
        - Do not place the temperature box too close to the edge, or overlapping any important details.
        - Style the temperature box to fit the overall image and art style.
        - Style the pets to fit the activity and weather conditions.
        """,
    )


def generate_image(
    provider: str,
    client: Any,
    data: GenerateRequest,
    activity: str,
    input_images: dict[str, Image.Image],
    art_style: str,
) -> Image.Image:
    """Generate a cartoon image of pets based on forecast and activity."""
    include_reference_images = provider == "gemini"
    image_generation_prompt = _build_image_generation_prompt(
        data,
        activity,
        input_images,
        art_style,
        include_reference_images,
    )

    if provider == "gemini":
        if client is None:
            msg = "Gemini client is required for provider=gemini"
            raise RuntimeError(msg)
        if types is None:
            msg = "Gemini types unavailable: google-genai package is not installed"
            raise RuntimeError(msg)

        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=[image_generation_prompt, *input_images.values()],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio=data.image_gen_aspect_ratio,
                    image_size=data.image_gen_resolution,
                ),
            ),
        )

        if not response.parts:
            msg = "Gemini returned no image."
            raise RuntimeError(msg)

        for part in response.parts:
            img = part.as_image()
            if img and img.image_bytes:
                img_pil = Image.open(io.BytesIO(img.image_bytes))
                return img_pil.copy()

        msg = "No image part in response."
        raise RuntimeError(msg)

    response = _openrouter_post(
        "/chat/completions",
        {
            "model": data.openrouter_image_model,
            "messages": [{"role": "user", "content": image_generation_prompt}],
            "modalities": ["image", "text"],
            "stream": False,
            "image_config": {
                "aspect_ratio": data.image_gen_aspect_ratio,
            },
        },
        data.openrouter_api_key,
    )

    choices = response.get("choices", [])
    if not choices:
        msg = "OpenRouter returned no image choices."
        raise RuntimeError(msg)
    images = choices[0].get("message", {}).get("images", [])
    if not images:
        msg = "OpenRouter returned no images in chat completion response."
        raise RuntimeError(msg)

    image_url = images[0].get("image_url", {}).get("url")
    if not image_url:
        msg = "OpenRouter image response missing image_url.url."
        raise RuntimeError(msg)
    if image_url.startswith("data:image"):
        _, encoded = image_url.split(",", maxsplit=1)
        image_bytes = base64.b64decode(encoded)
        img_pil = Image.open(io.BytesIO(image_bytes))
        return img_pil.copy()
    with urllib.request.urlopen(image_url, timeout=60) as image_response:
        image_bytes = image_response.read()
    img_pil = Image.open(io.BytesIO(image_bytes))
    return img_pil.copy()


def _openrouter_post(path: str, payload: dict, api_key: str | None) -> dict:
    if not api_key:
        msg = "OpenRouter API key is required."
        raise RuntimeError(msg)

    request = urllib.request.Request(
        f"{_OPENROUTER_API_BASE}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        msg = f"OpenRouter request failed ({exc.code}): {detail}"
        raise RuntimeError(msg) from exc


def _extract_openrouter_text(content: object) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts).strip()
    return ""
