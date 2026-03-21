"""Config flow for Forecats."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PROVIDERS = ["gemini", "openrouter"]


class ForecastsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Forecats."""

    VERSION = 1

    def __init__(self) -> None:
        self._provider: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Step 1: select provider."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            self._provider = user_input["provider"]
            if self._provider == "gemini":
                return await self.async_step_gemini()
            return await self.async_step_openrouter()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("provider", default="gemini"): vol.In(PROVIDERS),
                }
            ),
        )

    async def async_step_gemini(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Step 2a: collect Gemini API key."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if not user_input.get("gemini_api_key", "").strip():
                errors["gemini_api_key"] = "empty_api_key"
            else:
                return self.async_create_entry(
                    title="Forecats",
                    data={
                        "provider": "gemini",
                        "gemini_api_key": user_input["gemini_api_key"].strip(),
                    },
                )

        return self.async_show_form(
            step_id="gemini",
            data_schema=vol.Schema(
                {
                    vol.Required("gemini_api_key"): str,
                }
            ),
            errors=errors,
        )

    async def async_step_openrouter(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Step 2b: collect OpenRouter credentials and models."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if not user_input.get("openrouter_api_key", "").strip():
                errors["openrouter_api_key"] = "empty_api_key"
            elif not user_input.get("openrouter_text_model", "").strip():
                errors["openrouter_text_model"] = "empty_model"
            elif not user_input.get("openrouter_image_model", "").strip():
                errors["openrouter_image_model"] = "empty_model"
            else:
                return self.async_create_entry(
                    title="Forecats",
                    data={
                        "provider": "openrouter",
                        "openrouter_api_key": user_input["openrouter_api_key"].strip(),
                        "openrouter_text_model": user_input[
                            "openrouter_text_model"
                        ].strip(),
                        "openrouter_image_model": user_input[
                            "openrouter_image_model"
                        ].strip(),
                    },
                )

        return self.async_show_form(
            step_id="openrouter",
            data_schema=vol.Schema(
                {
                    vol.Required("openrouter_api_key"): str,
                    vol.Required("openrouter_text_model"): str,
                    vol.Required("openrouter_image_model"): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Return the options flow handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Forecats (edit credentials)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    def _get_value(self, key: str, default: str = "") -> str:
        """Return current value, preferring options over data."""
        return self._config_entry.options.get(
            key, self._config_entry.data.get(key, default)
        )

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Route to the correct provider step."""
        provider = self._config_entry.data.get("provider", "gemini")
        if provider == "gemini":
            return await self.async_step_gemini(user_input)
        return await self.async_step_openrouter(user_input)

    async def async_step_gemini(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Update Gemini API key."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if not user_input.get("gemini_api_key", "").strip():
                errors["gemini_api_key"] = "empty_api_key"
            else:
                return self.async_create_entry(
                    title="",
                    data={
                        "provider": "gemini",
                        "gemini_api_key": user_input["gemini_api_key"].strip(),
                    },
                )

        current_key = self._get_value("gemini_api_key")
        return self.async_show_form(
            step_id="gemini",
            data_schema=vol.Schema(
                {
                    vol.Required("gemini_api_key", default=current_key): str,
                }
            ),
            errors=errors,
        )

    async def async_step_openrouter(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Update OpenRouter credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if not user_input.get("openrouter_api_key", "").strip():
                errors["openrouter_api_key"] = "empty_api_key"
            elif not user_input.get("openrouter_text_model", "").strip():
                errors["openrouter_text_model"] = "empty_model"
            elif not user_input.get("openrouter_image_model", "").strip():
                errors["openrouter_image_model"] = "empty_model"
            else:
                return self.async_create_entry(
                    title="",
                    data={
                        "provider": "openrouter",
                        "openrouter_api_key": user_input["openrouter_api_key"].strip(),
                        "openrouter_text_model": user_input[
                            "openrouter_text_model"
                        ].strip(),
                        "openrouter_image_model": user_input[
                            "openrouter_image_model"
                        ].strip(),
                    },
                )

        return self.async_show_form(
            step_id="openrouter",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "openrouter_api_key",
                        default=self._get_value("openrouter_api_key"),
                    ): str,
                    vol.Required(
                        "openrouter_text_model",
                        default=self._get_value("openrouter_text_model"),
                    ): str,
                    vol.Required(
                        "openrouter_image_model",
                        default=self._get_value("openrouter_image_model"),
                    ): str,
                }
            ),
            errors=errors,
        )
