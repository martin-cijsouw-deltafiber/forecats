# test.py
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from forecats import generate_pet_pic
from models import GenerateRequest, Pet

load_dotenv()  # Load environment variables from a .env file if present


TEST_DIR = "."

input_image_paths = [
    "./forecats_data/input_images/milo.jpg",
    "./forecats_data/input_images/milo_and_tolmie.jpg",
    "./forecats_data/input_images/tolmie.jpg",
    "./forecats_data/input_images/milo_and_tolmie_2.jpg",
    "./forecats_data/input_images/tolmie_2.jpg",
]

data = GenerateRequest(
    provider=os.getenv("GEN_PROVIDER")
    or (
        "openrouter"
        if (
            os.getenv("OPENROUTER_API_KEY")
            and os.getenv("OPENROUTER_TEXT_MODEL")
            and os.getenv("OPENROUTER_IMAGE_MODEL")
        )
        else "gemini"
    ),
    gemini_api_key=os.getenv("GEMINI_API_KEY"),
    openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
    openrouter_text_model=os.getenv("OPENROUTER_TEXT_MODEL"),
    openrouter_image_model=os.getenv("OPENROUTER_IMAGE_MODEL"),
    location="Toronto, Ontario, Canada",
    forecast={"datetime": "2025-6-07", "temperature": -10, "templow": -15, "condition": "sunny"},
    temperature_unit="C",
    pets=[
        Pet(
            name="Milo",
            type="cat",
            description="Milo is a domestic short-haired tabby. He is seven years old and we like to imagine that he is serious but a little goofy on the outside. He has green eyes, with big pupils when he is excited. He loves cuddling, sitting on his moms lap, his little brother Tolmie, holding little pom-poms in his mouth, and stealing kibbles from his brother. You can just *barely* see a little bit of his pink skin beneath his tummy fur, but it is cute and fuzzy with some paunch. He has cute white paws and a white tummy.",
        ),
        Pet(
            name="Tolmie",
            type="cat",
            description="Tolmie is a ragdoll, he has pretty blue eyes, and his black pupils get big when he's excited. We like to imagine that he is goofy. He loves his big brother Milo, playing with strings, rolling on the ground belly-up, and sprinting full speed around the house yelling. He is a little bigger (longer) than Milo, and all fluff. When he is happy he likes to stick his tail up.",
        ),
        Pet(
            name="Brutus",
            type="dog",
            description="Brutus is a golden retriever. He is a year old and we like to imagine that he is playful and energetic. He has brown eyes, with big pupils when he is excited. He loves playing fetch, running around the yard, and cuddling with his family. He is a little bigger (longer) than Tolmie, and all fluff. When he is happy he likes to stick his tail up.",
        ),
    ],
    input_image_paths=input_image_paths,
    art_styles=[
        "comic book",
        "anime",
        "pixar",
        "watercolor",
        "ghibli",
        "disney",
    ],
    image_gen_aspect_ratio="16:9",
    image_gen_resolution="1K",
    final_image_size="800x480",
    display_profile="spectra6",
)

# Call the function and save the result
img = generate_pet_pic(data, TEST_DIR)
