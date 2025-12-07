import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall

from .forecats import generate_cat_pic
from .models import GenerateRequest

DOMAIN = "forecats"
_LOGGER = logging.getLogger(__name__)

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required("gemini_api_key"): cv.string,
        vol.Required("location"): cv.string,
        vol.Required("forecast"): dict,
        vol.Required("cat_names"): [cv.string],
        vol.Required("cat_descriptions"): [cv.string],
        vol.Required("input_image_paths"): [cv.string],
        vol.Required("art_styles"): [cv.string],
        vol.Required("image_gen_aspect_ratio"): cv.string,
        vol.Required("image_gen_resolution"): cv.string,
        vol.Required("final_image_size"): cv.string,
        vol.Optional("display_profile"): cv.string,
    },
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the cat generator integration."""

    async def handle_generate(call: ServiceCall) -> None:
        data = GenerateRequest(
            **call.data,
        )  # look I know I validate twice but I cant be effed to refactor

        try:
            # Run in executor thread, pass HA config directory
            original_path, optimized_path = await hass.async_add_executor_job(
                generate_cat_pic,
                data,
                hass.config.path(),
            )

            _LOGGER.info(f"Generated cat pictures: {original_path}, {optimized_path}")

        except Exception:
            _LOGGER.exception("Failed to generate cat picture")

    hass.services.async_register(
        DOMAIN, "generate_cat_picture", handle_generate, SERVICE_SCHEMA
    )

    return True
