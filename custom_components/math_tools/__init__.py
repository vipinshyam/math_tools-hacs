from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

DOMAIN = "math_tools"
CONF_BASE_URL = "base_url"
CONF_API_KEY = "api_key"

PostFn = Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    # No YAML setup required; UI config flow will handle it.
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)

    def _get_cfg() -> tuple[str, str | None]:
        base = (entry.options.get(CONF_BASE_URL) or entry.data.get(CONF_BASE_URL) or "http://127.0.0.1:8000").rstrip("/")
        key = entry.options.get(CONF_API_KEY) or entry.data.get(CONF_API_KEY)
        return base, key

    async def _post(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        base_url, api_key = _get_cfg()
        url = f"{base_url}/{endpoint.lstrip('/')}"
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-API-Key"] = api_key
        async with session.post(url, json=payload, headers=headers) as resp:
            data = await resp.json(content_type=None)
            if resp.status >= 400:
                raise RuntimeError(f"{resp.status}: {data}")
            return data

    # Register services once (single instance enforced by config_flow)
    def _svc_exists(name: str) -> bool:
        return hass.services.has_service(DOMAIN, name)

    async def _register_binary_service(name: str, endpoint: str):
        if _svc_exists(name):
            return

        async def _handler(call: ServiceCall) -> None:
            a = float(call.data["a"])
            b = float(call.data["b"])
            await _post(endpoint, {"a": a, "b": b})

        hass.services.async_register(DOMAIN, name, _handler)

    async def _register_values_service(name: str, endpoint: str, extra_fields: list[str] | None = None):
        if _svc_exists(name):
            return

        async def _handler(call: ServiceCall) -> None:
            values = call.data.get("values")
            if isinstance(values, str):
                values = [float(x.strip()) for x in values.split(",") if x.strip()]
            elif isinstance(values, list):
                values = [float(x) for x in values]
            else:
                values = []
            payload: dict[str, Any] = {"values": values}
            if extra_fields:
                for f in extra_fields:
                    if f in call.data:
                        payload[f] = call.data[f]
            await _post(endpoint, payload)

        hass.services.async_register(DOMAIN, name, _handler)

    # Math endpoints
    await _register_binary_service("add", "/math/add")
    await _register_binary_service("subtract", "/math/subtract")
    await _register_binary_service("multiply", "/math/multiply")

    if not _svc_exists("divide"):
        async def divide(call: ServiceCall) -> None:
            a = float(call.data["a"]); b = float(call.data["b"])
            await _post("/math/divide", {"a": a, "b": b})
        hass.services.async_register(DOMAIN, "divide", divide)

    if not _svc_exists("power"):
        async def power(call: ServiceCall) -> None:
            base = float(call.data["base"]); exponent = float(call.data["exponent"])
            await _post("/math/power", {"base": base, "exponent": exponent})
        hass.services.async_register(DOMAIN, "power", power)

    await _register_values_service("mean", "/math/mean")
    await _register_values_service("median", "/math/median")

    if not _svc_exists("std"):
        async def std(call: ServiceCall) -> None:
            values = call.data.get("values")
            if isinstance(values, str):
                values = [float(x.strip()) for x in values.split(",") if x.strip()]
            else:
                values = [float(x) for x in values]
            sample = bool(call.data.get("sample", False))
            await _post("/math/std", {"values": values, "sample": sample})
        hass.services.async_register(DOMAIN, "std", std)

    for name, endpoint in (("gcd", "/algorithms/gcd"), ("lcm", "/algorithms/lcm")):
        if not _svc_exists(name):
            async def _handler(call: ServiceCall, ep=endpoint) -> None:
                a = int(call.data["a"]); b = int(call.data["b"])
                await _post(ep, {"a": a, "b": b})
            hass.services.async_register(DOMAIN, name, _handler)

    if not _svc_exists("is_prime"):
        async def is_prime(call: ServiceCall) -> None:
            n = int(call.data["n"])
            await _post("/algorithms/is_prime", {"n": n})
        hass.services.async_register(DOMAIN, "is_prime", is_prime)

    if not _svc_exists("prime_factors"):
        async def prime_factors(call: ServiceCall) -> None:
            n = int(call.data["n"])
            await _post("/algorithms/prime_factors", {"n": n})
        hass.services.async_register(DOMAIN, "prime_factors", prime_factors)

    if not _svc_exists("fibonacci"):
        async def fibonacci(call: ServiceCall) -> None:
            n = int(call.data["n"])
            await _post("/algorithms/fibonacci", {"n": n})
        hass.services.async_register(DOMAIN, "fibonacci", fibonacci)

    await _register_values_service("sort", "/algorithms/sort", ["reverse"])

    for name, endpoint in (
        ("moving_average", "/algorithms/moving_average"),
        ("rolling_min", "/algorithms/rolling_min"),
        ("rolling_max", "/algorithms/rolling_max"),
    ):
        if not _svc_exists(name):
            async def _handler(call: ServiceCall, ep=endpoint) -> None:
                values = call.data.get("values")
                if isinstance(values, str):
                    values = [float(x.strip()) for x in values.split(",") if x.strip()]
                else:
                    values = [float(x) for x in values]
                window = int(call.data["window"])
                await _post(ep, {"values": values, "window": window})
            hass.services.async_register(DOMAIN, name, _handler)

    # Register intents for Assist/LLMs
    try:
        from .intent import async_register_intents
        await async_register_intents(hass, _post)
    except Exception as e:
        hass.logger.error("math_tools: intent registration failed: %s", e)

    # Reload when options change
    async def _update_listener(hass: HomeAssistant, entry: ConfigEntry):
        await hass.config_entries.async_reload(entry.entry_id)

    entry.async_on_unload(entry.add_update_listener(_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Nothing platform-based to unload; just clear data if you store any.
    return True
