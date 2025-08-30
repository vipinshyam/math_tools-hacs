from __future__ import annotations

import os
from typing import Any, Awaitable, Callable

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.aiohttp_client import async_get_clientsession

DOMAIN = "math_tools"

PostFn = Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Math Tools: register services and intents for Assist/LLM tool use."""
    session = async_get_clientsession(hass)

    # Configure where your FastAPI math server is running.
    # You can override these via environment variables on the HA host.
    base_url = os.environ.get("MATH_TOOLS_BASE_URL", "http://172.16.2.223:8111").rstrip("/")
    api_key = os.environ.get("MATH_TOOLS_API_KEY")

    async def _post(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{base_url}/{endpoint.lstrip('/')}"
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-API-Key"] = api_key
        async with session.post(url, json=payload, headers=headers) as resp:
            data = await resp.json(content_type=None)
            if resp.status >= 400:
                raise RuntimeError(f"{resp.status}: {data}")
            return data  # expected to contain {"result": ...}

    # Helper to register simple two-number services
    async def _register_binary_service(name: str, endpoint: str):
        async def _handler(call: ServiceCall) -> None:
            a = float(call.data["a"])  # required by services.yaml
            b = float(call.data["b"])  # required by services.yaml
            await _post(endpoint, {"a": a, "b": b})
        hass.services.async_register(DOMAIN, name, _handler)

    # Simple list services (values: list[float])
    async def _register_values_service(name: str, endpoint: str, extra_fields: list[str] | None = None):
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

    # Individual service registrations (discoverable to LLMs as tools)
    await _register_binary_service("add", "/math/add")
    await _register_binary_service("subtract", "/math/subtract")
    await _register_binary_service("multiply", "/math/multiply")

    async def divide(call: ServiceCall) -> None:
        a = float(call.data["a"]) ; b = float(call.data["b"]) ; await _post("/math/divide", {"a": a, "b": b})
    hass.services.async_register(DOMAIN, "divide", divide)

    async def power(call: ServiceCall) -> None:
        base = float(call.data["base"]) ; exponent = float(call.data["exponent"]) ; await _post("/math/power", {"base": base, "exponent": exponent})
    hass.services.async_register(DOMAIN, "power", power)

    await _register_values_service("mean", "/math/mean")
    await _register_values_service("median", "/math/median")

    async def std(call: ServiceCall) -> None:
        values = call.data.get("values")
        if isinstance(values, str):
            values = [float(x.strip()) for x in values.split(",") if x.strip()]
        else:
            values = [float(x) for x in values]
        sample = bool(call.data.get("sample", False))
        await _post("/math/std", {"values": values, "sample": sample})
    hass.services.async_register(DOMAIN, "std", std)

    async def gcd(call: ServiceCall) -> None:
        a = int(call.data["a"]) ; b = int(call.data["b"]) ; await _post("/algorithms/gcd", {"a": a, "b": b})
    hass.services.async_register(DOMAIN, "gcd", gcd)

    async def lcm(call: ServiceCall) -> None:
        a = int(call.data["a"]) ; b = int(call.data["b"]) ; await _post("/algorithms/lcm", {"a": a, "b": b})
    hass.services.async_register(DOMAIN, "lcm", lcm)

    async def is_prime(call: ServiceCall) -> None:
        n = int(call.data["n"]) ; await _post("/algorithms/is_prime", {"n": n})
    hass.services.async_register(DOMAIN, "is_prime", is_prime)

    async def prime_factors(call: ServiceCall) -> None:
        n = int(call.data["n"]) ; await _post("/algorithms/prime_factors", {"n": n})
    hass.services.async_register(DOMAIN, "prime_factors", prime_factors)

    async def fibonacci(call: ServiceCall) -> None:
        n = int(call.data["n"]) ; await _post("/algorithms/fibonacci", {"n": n})
    hass.services.async_register(DOMAIN, "fibonacci", fibonacci)

    await _register_values_service("sort", "/algorithms/sort", ["reverse"])

    async def moving_average(call: ServiceCall) -> None:
        values = call.data.get("values")
        if isinstance(values, str):
            values = [float(x.strip()) for x in values.split(",") if x.strip()]
        else:
            values = [float(x) for x in values]
        window = int(call.data["window"]) ; await _post("/algorithms/moving_average", {"values": values, "window": window})
    hass.services.async_register(DOMAIN, "moving_average", moving_average)

    async def rolling_min(call: ServiceCall) -> None:
        values = call.data.get("values")
        if isinstance(values, str):
            values = [float(x.strip()) for x in values.split(",") if x.strip()]
        else:
            values = [float(x) for x in values]
        window = int(call.data["window"]) ; await _post("/algorithms/rolling_min", {"values": values, "window": window})
    hass.services.async_register(DOMAIN, "rolling_min", rolling_min)

    async def rolling_max(call: ServiceCall) -> None:
        values = call.data.get("values")
        if isinstance(values, str):
            values = [float(x.strip()) for x in values.split(",") if x.strip()]
        else:
            values = [float(x) for x in values]
        window = int(call.data["window"]) ; await _post("/algorithms/rolling_max", {"values": values, "window": window})
    hass.services.async_register(DOMAIN, "rolling_max", rolling_max)

    try:
        from .intent import async_register_intents
        await async_register_intents(hass, _post)
    except Exception as e:
        # Log and continue so services are still available
        hass.logger.error("math_tools: intent registration failed: %s", e)

    return True
