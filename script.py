import random
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image
import textwrap

# DELETE THESE LINES FOR PRODUCTION
from dotenv import load_dotenv
import os

load_dotenv()


class Data:
    api_key: str | None
    input_image_paths: list[str]
    output_image_dir: str
    forecast: dict
    location: str
    cat_names: list[str]
    cat_descriptions: list[str]
    cat_activities: list[str]
    art_styles: list[str]
    image_gen_aspect_ratio: str
    image_gen_resolution: str
    final_aspect_ratio: str
    final_resolution: str


def load_config():
    data = Data()
    data.api_key = os.getenv("GEMINI_API_KEY")
    data.input_image_paths = [
        "./inputs/milo_and_tolmie.jpg",
        "./inputs/milo_and_tolmie2.jpg",
        "./inputs/milo.jpg",
        "./inputs/tolmie.jpg",
        "./inputs/tolmie2.jpg",
    ]
    data.output_image_dir = "./outputs"
    data.location = "Toronto, Ontario, Canada"
    data.forecast = {
        "datetime": "2024-12-04T14:00:00+00:00",
        "is_daytime": True,
        "apparent_temperature": -8.5,
        "cloud_coverage": 75,
        "condition": "Snowy",
        "dew_point": -12.0,
        "humidity": 65,
        "precipitation_probability": 30,
        "precipitation": 0,
        "pressure": 1015,
        "temperature": -3.0,
        "templow": -7.0,
        "uv_index": 1,
        "wind_bearing": 315,
        "wind_gust_speed": 25.0,
        "wind_speed": 18.0,
    }
    data.cat_names = ["Milo", "Tolmie"]
    data.cat_descriptions = [
        "Milo is a domestic short-haired tabby. He is seven years old and we like to imagine that he is serious on the outside, but goofy and cuddly on the inside. He loves sitting on his mom's lap, his little brother Tolmie, holding pom-pom toys in his mouth, and stealing kibbles from his brother. His belly is a little pink, because he has licked some fur off, but it is cute and fuzzy with some paunch.",
        "Tolmie is a blue sealpoint ragdoll, just a smidge cross-eyed. We like to imagine that he is pretty goofy. He loves his big brother Milo, playing with strings, rolling on the ground (belly up), and sprinting full speed around the house yelling. He is all fluff.",
    ]
    data.art_styles = [
        "comic book",
        "anime",
        "pixar",
        "watercolor",
        "ghibli",
        "disney",
        "scavengers reign style",
        "Traditional 2D Animation Style",
        "Cel Animation Style",
        "Stop-Motion Animation Style",
        "Claymation Style",
        "Puppetoon Style",
        "Jean Giraud/Moebius Style",
        "Banksy Style",
        "Vintage Cartoon Style",
        "Cutout Animation Style",
        "3D/CGI Animation Style",
        "Pixar Style",
        "Stylized 3D Animation Style",
        "Motion Graphics Animation Style",
        "Rotoscoping Style",
        "Limited Animation Style",
        "Full Animation Style",
        "Anime Style",
        "Chibi Style",
        "Ghibli Style",
        "Rubber Hose Animation Style",
        "Fleischer Style",
        "Looney Tunes Style",
        "U.P.A. (United Productions of America) Style",
        "South Park Style",
        "The Simpsons Style",
        "Adult Swim Style",
        "Abstract Animation Style",
        "Pin Screen Animation Style",
        "Sand Animation Style",
        "Watercolor Animation Style",
        "Line Drawing Animation Style",
        "Splatterscreen/Hanna-Barbera Style",
        "Experimental Animation Style",
    ]
    data.image_gen_aspect_ratio = "16:9"
    data.image_gen_resolution = "1K"
    data.final_aspect_ratio = "5:3"
    data.final_resolution = "800x480"

    return data


###################################################
PROMPT_HISTORY_FILEPATH = "./inputs/prompt_history.txt"


def load_prompt_history(filepath):
    """Load past prompts from file."""
    path = Path(filepath)
    if path.exists():
        return path.read_text().splitlines()
    path.parent.mkdir(parents=True, exist_ok=True)
    return []


def save_prompt_history(filepath, history):
    """Save prompt history to file."""
    Path(filepath).write_text("\n".join(history))


def load_images(paths, max_size=1024):
    """Load and resize images."""

    def resize(img_path):
        img = Image.open(img_path)
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        return img

    valid_paths = [Path(p) for p in paths if Path(p).exists()]
    return {p.name: resize(p) for p in valid_paths}


def generate_activity(client, data, prompt_history) -> str:
    activity_prompt = textwrap.dedent(
        f"""
        You are a prompt generator for static AI cartoon art generation model. Your task is to generate an activity for {len(data.cat_names)} cats to do based on the date and weather conditions provided, which will be used to draw a single picture.

        The date is {data.forecast["datetime"]}. 

        The weather forecast is for {data.location}. 

        The forecast is:
        {data.forecast}

        The last 20 activities you generated were:
        {prompt_history}

        Follow this prompt: 

        Generate a fun activity for {len(data.cat_names)} cats to do together that fits the weather conditions and time of year. 

        Heuristics:
        - You can anthropomorphize the cats to do human-like activities, or you can make them do more cat-like activities occasionally.
        - The activity can be either indoors or outdoors, but should be appropriate for the weather conditions and time of year.
        - Activities should be 30% set in Toronto, and 20% set in other specific locations with similar weather, and 50% set in generic locations.
        - Be creative and imaginative.
        - The mix of indoor/outdoor should be seasonally appropriate. Summer is more outdoor, winter is more indoor.
        - It can be a mundane activity (waiting for the bus, commuting, shopping, reading, etc.) or something more exciting (playing in the snow, going to a festival, playing tag, chess, etc.).
        - Try to keep it different from the last 20 activities you generated (e.g., if there are lots that are outdoors, maybe make an indoor one. Lots of mundane ones? make an exciting one!).

        Rules: 
        - Do not take weather into account when making indoor/outdoor decision, only take season and past prompts.
        - You don't have to describe the weather, as this will also be in the final prompt for the art generation model.
        - The activity should involve all {len(data.cat_names)} cats
        - Don't repeat any of the last 20 activities you generated
        - There should only be one activity described
        - Respond in a single line, no more than 50 words
        - Do not use newlines
        """
    )

    activity_response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=activity_prompt,
    )

    return activity_response.text


def generate_image(client, data, activity, input_images, art_style):
    image_generation_prompt = textwrap.dedent(
        f"""
        You are an AI artist creating daily weather illustrations featuring cats based on a weather forecast and an activity that will be given to you. Your task is to generate a vibrant and engaging illustration that captures the essence of the weather conditions and the cats' activity in a specific art style.

        The weather forecast is for {data.location} on {data.forecast["datetime"]}:
        {data.forecast}

        You have {len(data.cat_names)} cats to illustrate:
        {", ".join(data.cat_names)}.

        Here are their descriptions:
        {"\n- ".join(data.cat_descriptions)}

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
        - The final image will be cropped  in postprocessing to aspect ratio {data.final_aspect_ratio} and resolution {data.final_resolution}, so compose the image accordingly and avoid placing important elements at the edges.
        """
    )

    client = genai.Client(api_key=data.api_key)

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
    if response and response.parts:
        for part in response.parts:
            if image := part.as_image():
                return image

    return None


def main():
    data = load_config()

    # setup
    output_dir = Path(data.output_image_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # load resources
    prompt_history = load_prompt_history(PROMPT_HISTORY_FILEPATH)
    images = load_images(data.input_image_paths)
    art_style = random.choice(data.art_styles)
    print(f"Selected art style: {art_style}")  # TODO takeout

    # Generate activity description
    # TODO add an if-else to allow for date/activity overrides on particular days
    client = genai.Client(api_key=data.api_key)
    activity = generate_activity(client, data, prompt_history)
    print(activity)  # TODO takeout

    # Update prompt history
    prompt_history.append(activity)
    prompt_history = prompt_history[-20:]
    save_prompt_history(PROMPT_HISTORY_FILEPATH, prompt_history)

    # Generate image
    image = generate_image(client, data, activity, images, art_style)
    output_path = output_dir / f"cat_weather_{data.forecast['datetime'][:10]}.png"
    if image:
        image.save(str(output_path))
        print(f"Saved image to {output_path}")
    else:
        print("Failed to generate image.")


if __name__ == "__main__":
    main()
