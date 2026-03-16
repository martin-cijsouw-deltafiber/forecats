import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from .forecats import generate_pet_pic
from .models import GenerateRequest

DOMAIN = "forecats"
_LOGGER = logging.getLogger(__name__)

PET_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.string,
        vol.Required("description"): cv.string,
        vol.Required("type", default="cat"): cv.string,
    }
)

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Optional("provider", default="gemini"): vol.In(["gemini", "openrouter"]),
        vol.Optional("gemini_api_key"): cv.string,
        vol.Optional("openrouter_api_key"): cv.string,
        vol.Optional("openrouter_text_model"): cv.string,
        vol.Optional("openrouter_image_model"): cv.string,
        vol.Required("location"): cv.string,
        vol.Required("forecast"): dict,
        vol.Required("temperature_unit"): cv.string,
        vol.Required("pets"): list[PET_SCHEMA],
        vol.Required("input_image_paths"): [cv.string],
        vol.Required("art_styles"): [cv.string],
        vol.Required("image_gen_aspect_ratio"): cv.string,
        vol.Required("image_gen_resolution"): cv.string,
        vol.Required("final_image_size"): cv.string,
        vol.Optional("display_profile"): cv.string,
    },
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the pet generator integration."""

    def _validate_provider_fields(call_data: dict) -> None:
        provider = (call_data.get("provider") or "gemini").lower()
        if provider == "gemini":
            if not call_data.get("gemini_api_key"):
                msg = "provider=gemini requires gemini_api_key"
                raise HomeAssistantError(msg)
            return
        if provider == "openrouter":
            required_fields = (
                "openrouter_api_key",
                "openrouter_text_model",
                "openrouter_image_model",
            )
            missing = [field for field in required_fields if not call_data.get(field)]
            if missing:
                msg = f"provider=openrouter missing required fields: {', '.join(missing)}"
                raise HomeAssistantError(msg)
            return
        msg = f"Unsupported provider: {provider}"
        raise HomeAssistantError(msg)

    async def handle_generate(call: ServiceCall) -> None:
        _validate_provider_fields(call.data)
        data = GenerateRequest(
            **call.data,
        )  # look I know I validate twice but I cant be effed to refactor
        _LOGGER.info(
            "Received generate_pet_picture call (provider=%s, location=%s, pets=%s, images=%s, art_styles=%s)",
            data.provider,
            data.location,
            len(data.pets),
            len(data.input_image_paths),
            len(data.art_styles),
        )
        # Run in executor thread, pass HA config directory
        original_path, optimized_path = await hass.async_add_executor_job(
            generate_pet_pic,
            data,
            hass.config.path(),
        )

        _LOGGER.info(f"Generated pet pictures: {original_path}, {optimized_path}")

    hass.services.async_register(DOMAIN, "generate_pet_picture", handle_generate, SERVICE_SCHEMA)

    return True
