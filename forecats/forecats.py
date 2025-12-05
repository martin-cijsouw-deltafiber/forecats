"""Generate cat pictures based on weather forecasts using Gemini."""

import io
import logging
import os
import random
import textwrap
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()


def generate_cat_pic(data: dict) -> Image.Image:
    """Generate, crop, and dither a cat picture based on the current weather using gemini.

    Data dictionary keys:
    """
    logger = logging.getLogger(Path(__file__).stem)

    # load resources
    prompt_history_filepath = Path("./data/forecats_prompt_history.txt")
    prompt_history = load_prompt_history(prompt_history_filepath)
    images = load_images(data.get("input_image_paths", []))
    art_style = random.choice(data.get("art_styles", []))

    logger.debug(f"Selected art style: {art_style}")

    # Generate activity description
    # TODO add an if-else to allow for date/activity overrides on particular days
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    activity = generate_activity(client, data, prompt_history)

    logger.debug(f"Generated activity: {activity}")

    # Update prompt history
    prompt_history.append(activity)
    prompt_history = prompt_history[-20:]
    save_prompt_history(prompt_history_filepath, prompt_history)

    # # Generate image
    # image = generate_image(client, data, activity, images, art_style)

    return activity


def load_prompt_history(filepath: Path) -> list[str]:
    """Load past prompts from file."""
    path = Path(filepath)
    if path.exists():
        return path.read_text().splitlines()
    path.parent.mkdir(parents=True, exist_ok=True)
    return []


def save_prompt_history(filepath: Path, history: list[str]) -> None:
    """Save prompt history to file."""
    Path(filepath).write_text("\n".join(history))


def load_images(paths: list[Path], max_size: int = 1024) -> dict[str, Image.Image]:
    """Load and resize images."""

    def resize(img_path: Path) -> Image.Image:
        img = Image.open(img_path)
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        return img

    valid_paths = [Path(p) for p in paths if Path(p).exists()]
    return {p.name: resize(p) for p in valid_paths}


def generate_activity(client: genai.Client, data: dict, prompt_history: list[str]) -> str:
    """Describe an activity for the cats based on the weather forecast and date."""
    activity_prompt = textwrap.dedent(
        f"""
        You are a prompt generator for static AI cartoon art generation model. Your task is to generate an activity for {len(data.get("cat_names", []))} cats to do based on the date and weather conditions provided, which will be used to draw a single picture.

        The date is {data.get("forecast", {}).get("datetime", "")}.

        The weather forecast is for {data.get("location", "")}.

        The forecast is:
        {data.get("forecast", {})}

        The last 20 activities you generated were:
        {prompt_history}

        ************************************************

        Follow this prompt:

        Generate a fun activity for {len(data.get("cat_names", []))} cats to do together that fits the weather conditions and time of year.

        Heuristics:
        - You can anthropomorphize the cats to do human-like activities, or you can make them do more cat-like activities occasionally.
        - The activity can be either indoors or outdoors, but should be appropriate for the weather conditions and time of year.
        - Activities should be 30% set in Toronto, and 20% set in other specific locations with similar weather, and 50% set in generic locations.
        - Be creative and imaginative.
        - The mix of indoor/outdoor should be seasonally appropriate. Summer is more outdoor, winter is more indoor.
        - It can be a mundane activity (waiting for the bus, commuting, shopping, reading, etc.) or it can be exciting (playing in the snow, sports, going to a festival, playing tag, games, etc.).
        - Try to keep it different from the last 20 activities you generated (e.g., if there are lots that are outdoors, maybe make an indoor one. Lots of mundane ones? make an exciting one!).

        Rules:
        - Do not take weather into account when making indoor/outdoor decision, only take season and past prompts.
        - You don't have to describe the weather, as this will also be in the final prompt for the art generation model.
        - The activity should be able to involve all {len(data.get("cat_names", []))} cats
        - The activity must not be similar to any of the last 20 activities you generated.
        - There should only be one activity described
        - Respond in a single line, no more than 50 words
        - Do not use newlines
        - Do not describe the appearance of the cats, with the exception of clothing or accessories needed for the activity
        - Respond with "Activity: <activity>, description: <short description>"
        """,
    )

    activity_response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=activity_prompt,
    )

    if not activity_response.text:
        msg = "Gemini returned no activity."
        raise RuntimeError(msg)

    return activity_response.text


def generate_image(
    client: genai.Client,
    data: dict,
    activity: str,
    input_images: dict[str, Image.Image],
    art_style: str,
) -> Image.Image:
    """Generate a cartoon image of cats based on the weather forecast and activity using gemini."""
    image_generation_prompt = textwrap.dedent(
        f"""
        You are an AI artist creating daily weather illustrations featuring cats based on a weather forecast and an activity that will be given to you. Your task is to generate a vibrant and engaging illustration that captures the essence of the weather conditions and the cats' activity in a specific art style.

        The weather forecast is for {data.get("location", "")} on {data.get("forecast", {}).get("datetime", "")}:
        {data.get("forecast", {})}

        You have {len(data.get("cat_names", []))} cats to illustrate:
        {", ".join(data.get("cat_names", []))}.

        Here are their descriptions:
        {"\n- ".join(data.get("cat_descriptions", []))}

        The activity they are doing today is:
        {activity}

        The art style should be:
        {art_style}

        You will be given {len(input_images)} input images with these names (in this order):
        {", ".join(input_images.keys())}

        Create a vibrant and engaging illustration in the recommended style that captures the essence of the weather conditions and the cats' activity. Use colors and elements that reflect the forecasted weather, making the scene lively and appropriate for the time of year.

        Heuristics:
        - Try to capture the mood of the weather and activity in the illustration (e.g., bright and sunny, cozy indoors during snow, etc.).
        - Try to capture the cats personalities, but it is okay if they change based on the weather and activity.
        - This is for a color e-ink screen. I will handle the dithering later, but try to avoid very fine details that may be lost in dithering.

        Rules:
        - Only generate a single image.
        - Use the input images as references for the cats' appearances.
        - Style the cats to fit the activity and weather conditions.
        - The final image will be cropped in postprocessing to aspect ratio {data.get("final_aspect_ratio", "")} and resolution {data.get("final_resolution", "")}, so compose the image accordingly and DON'T place anything near the edges.
        """,
    )

    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[image_generation_prompt, *input_images.values()],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio=data.get("image_gen_aspect_ratio"),
                image_size=data.get("image_gen_resolution"),
            ),
        ),
    )

    if not response.parts:
        msg = "Gemini returned no image."
        raise RuntimeError(msg)
    for part in response.parts:
        if img := part.as_image():
            # Convert genai.types.Image to PIL Image using image_bytes
            if img.image_bytes:
                return Image.open(io.BytesIO(img.image_bytes))
            msg = "Image has no bytes data."
            raise RuntimeError(msg)

    msg = "No image part in response."
    raise RuntimeError(msg)
