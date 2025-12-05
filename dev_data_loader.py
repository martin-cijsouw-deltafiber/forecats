import os


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
        "Milo is a domestic short-haired tabby. He is seven years old and we like to imagine that he is serious but a little goofy on the outside. He loves cuddling, sitting on his mom's lap, his little brother Tolmie, holding pom-pom toys in his mouth, and stealing kibbles from his brother. You can just *barely* see a little bit of his pink skin beneath his tummy fur, but it is cute and fuzzy with some paunch.",
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
