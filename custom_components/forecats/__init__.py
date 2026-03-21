import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Stub for legacy YAML config — now handled via config entry."""
    if DOMAIN in config:
        _LOGGER.warning(
            "Configuring forecats via configuration.yaml is deprecated. "
            "Please remove the 'forecats:' entry and configure the integration "
            "through Settings → Integrations → Add → Forecats."
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Forecats from a config entry."""
    import homeassistant.helpers.config_validation as cv
    import voluptuous as vol

    from .forecats import generate_pet_pic
    from .models import GenerateRequest

    _LOGGER.info("forecats: async_setup_entry called — entry_id=%s", entry.entry_id)
    hass.data.setdefault(DOMAIN, {})
    # Merge options over data so credentials updated via "Configure" take effect
    # without requiring a full restart.
    hass.data[DOMAIN]["entry_data"] = {**entry.data, **entry.options}

    pet_schema = vol.Schema(
        {
            vol.Required("name"): cv.string,
            vol.Required("description"): cv.string,
            vol.Required("type", default="cat"): cv.string,
        }
    )

    service_schema = vol.Schema(
        {
            vol.Required("location"): cv.string,
            vol.Required("forecast"): dict,
            vol.Required("temperature_unit"): cv.string,
            vol.Required("pets"): [pet_schema],
            vol.Required("input_image_paths"): [cv.string],
            vol.Required("art_styles"): [cv.string],
            vol.Required("image_gen_aspect_ratio"): cv.string,
            vol.Required("image_gen_resolution"): cv.string,
            vol.Required("final_image_size"): cv.string,
            vol.Optional("display_profile"): cv.string,
            vol.Optional("output_dir"): cv.string,
        },
    )

    def _validate_provider_fields(merged: dict) -> None:
        provider = (merged.get("provider") or "gemini").lower()
        if provider == "gemini":
            if not merged.get("gemini_api_key"):
                msg = "provider=gemini requires gemini_api_key (configure via Settings → Integrations)"
                raise HomeAssistantError(msg)
            return
        if provider == "openrouter":
            required_fields = (
                "openrouter_api_key",
                "openrouter_text_model",
                "openrouter_image_model",
            )
            missing = [field for field in required_fields if not merged.get(field)]
            if missing:
                msg = (
                    f"provider=openrouter missing required fields: {', '.join(missing)} "
                    "(configure via Settings → Integrations)"
                )
                raise HomeAssistantError(msg)
            return
        msg = f"Unsupported provider: {provider}"
        raise HomeAssistantError(msg)

    async def handle_generate(call: ServiceCall) -> None:
        entry_data = hass.data[DOMAIN]["entry_data"]
        merged = {**entry_data, **call.data}
        _validate_provider_fields(merged)
        data = GenerateRequest(
            provider=entry_data["provider"],
            gemini_api_key=entry_data.get("gemini_api_key"),
            openrouter_api_key=entry_data.get("openrouter_api_key"),
            openrouter_text_model=entry_data.get("openrouter_text_model"),
            openrouter_image_model=entry_data.get("openrouter_image_model"),
            **call.data,
        )
        _LOGGER.info(
            "Received generate_pet_picture call (provider=%s, location=%s, pets=%s, images=%s, art_styles=%s)",
            data.provider,
            data.location,
            len(data.pets),
            len(data.input_image_paths),
            len(data.art_styles),
        )
        original_path, optimized_path = await hass.async_add_executor_job(
            generate_pet_pic,
            data,
            hass.config.path(),
        )
        _LOGGER.info("Generated pet pictures: %s, %s", original_path, optimized_path)

    hass.services.async_register(
        DOMAIN, "generate_pet_picture", handle_generate, service_schema
    )

    # Reload this entry whenever the user saves new options so credentials
    # take effect immediately without a manual HA restart.
    async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
        await hass.config_entries.async_reload(entry.entry_id)

    entry.async_on_unload(entry.add_update_listener(_async_update_options))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.services.async_remove(DOMAIN, "generate_pet_picture")
    hass.data[DOMAIN].pop("entry_data", None)
    return True

