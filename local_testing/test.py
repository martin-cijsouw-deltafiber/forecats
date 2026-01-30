# test.py
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from forecats import generate_cat_pic
from models import GenerateRequest
from dotenv import load_dotenv

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
    gemini_api_key=os.getenv("GEMINI_API_KEY"),
    location="Toronto, Ontario, Canada",
    forecast={"datetime": "2025-6-07", "temperature": -10, "templow": -15, "condition": "sunny"},
    temperature_unit="C",
    cat_names=["Milo", "Tolmie"],
    cat_descriptions=[
        "Milo is a domestic short-haired tabby. He is seven years old and we like to imagine that he is serious but a little goofy on the outside. He has green eyes, with big pupils when he is excited. He loves cuddling, sitting on his moms lap, his little brother Tolmie, holding little pom-poms in his mouth, and stealing kibbles from his brother. You can just *barely* see a little bit of his pink skin beneath his tummy fur, but it is cute and fuzzy with some paunch. He has cute white paws and a white tummy.",
        "Tolmie is a ragdoll, he has pretty blue eyes, and his black pupils get big when he's excited. We like to imagine that he is goofy. He loves his big brother Milo, playing with strings, rolling on the ground belly-up, and sprinting full speed around the house yelling. He is a little bigger (longer) than Milo, and all fluff. When he is happy he likes to stick his tail up.",
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
img = generate_cat_pic(data, TEST_DIR)
