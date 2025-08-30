from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

DOMAIN = "math_tools"
CONF_BASE_URL = "base_url"
CONF_API_KEY = "api_key"


def _schema(defaults: dict[str, str] | None = None) -> vol.Schema:
    d = defaults or {}
    return vol.Schema({
        vol.Required(CONF_BASE_URL, default=d.get(CONF_BASE_URL, "http://127.0.0.1:8000")): str,
        vol.Optional(CONF_API_KEY, default=d.get(CONF_API_KEY, "")): str,
    })


class MathToolsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        # Single instance only (keeps service registrations simple)
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=_schema())

        # Basic sanity check
        base = user_input[CONF_BASE_URL].strip().rstrip("/")
        if not (base.startswith("http://") or base.startswith("https://")):
            return self.async_show_form(
                step_id="user",
                data_schema=_schema(user_input),
                errors={"base_url": "invalid_url"},
            )

        return self.async_create_entry(
            title="Math Tools",
            data={
                CONF_BASE_URL: base,
                CONF_API_KEY: user_input.get(CONF_API_KEY, "").strip() or None,
            },
        )

    async def async_step_import(self, user_input):
        # Support YAML import if someone has `math_tools:` in configuration.yaml
        return await self.async_step_user(user_input)


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is None:
            defaults = {
                CONF_BASE_URL: self._entry.options.get(
                    CONF_BASE_URL, self._entry.data.get(CONF_BASE_URL, "http://127.0.0.1:8000")
                ),
                CONF_API_KEY: self._entry.options.get(
                    CONF_API_KEY, self._entry.data.get(CONF_API_KEY, "") or ""
                ),
            }
            return self.async_show_form(step_id="init", data_schema=_schema(defaults))

        # Save options
        opts = {
            CONF_BASE_URL: user_input[CONF_BASE_URL].strip().rstrip("/"),
            CONF_API_KEY: (user_input.get(CONF_API_KEY, "").strip() or None),
        }
        return self.async_create_entry(title="", data=opts)


async def async_get_options_flow(entry):
    return OptionsFlowHandler(entry)
