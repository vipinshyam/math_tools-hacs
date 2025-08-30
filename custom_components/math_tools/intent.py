from __future__ import annotations

from typing import Any, Awaitable, Callable

from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent

PostFn = Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]]


def _to_floats(maybe_values: Any) -> list[float]:
    if isinstance(maybe_values, str):
        return [float(x.strip()) for x in maybe_values.split(",") if x.strip()]
    if isinstance(maybe_values, list):
        return [float(x) for x in maybe_values]
    return []


class AddIntent(intent.IntentHandler):
    intent_type = "MathAdd"

    def __init__(self, post: PostFn) -> None:
        self._post = post

    async def async_handle(self, hass: HomeAssistant, intent_obj: intent.Intent) -> intent.IntentResponse:
        a = float(intent_obj.slots["a"]["value"])   # type: ignore[index]
        b = float(intent_obj.slots["b"]["value"])   # type: ignore[index]
        data = await self._post("/math/add", {"a": a, "b": b})
        res = data.get("result")
        r = intent.IntentResponse()
        r.async_set_speech(f"The sum of {a} and {b} is {res}.")
        r.async_set_card("Addition", f"{a} + {b} = {res}")
        return r


class FibonacciIntent(intent.IntentHandler):
    intent_type = "MathFibonacci"

    def __init__(self, post: PostFn) -> None:
        self._post = post

    async def async_handle(self, hass: HomeAssistant, intent_obj: intent.Intent) -> intent.IntentResponse:
        n = int(intent_obj.slots["n"]["value"])  # type: ignore[index]
        data = await self._post("/algorithms/fibonacci", {"n": n})
        seq = data.get("result", [])
        speak = ", ".join(map(str, seq[:30])) + (", and more" if len(seq) > 30 else "")
        r = intent.IntentResponse()
        r.async_set_speech(f"The Fibonacci sequence up to {n} terms is: {speak}.")
        r.async_set_card("Fibonacci", f"n={n}: {seq}")
        return r


class IsPrimeIntent(intent.IntentHandler):
    intent_type = "MathIsPrime"

    def __init__(self, post: PostFn) -> None:
        self._post = post

    async def async_handle(self, hass: HomeAssistant, intent_obj: intent.Intent) -> intent.IntentResponse:
        n = int(intent_obj.slots["n"]["value"])  # type: ignore[index]
        data = await self._post("/algorithms/is_prime", {"n": n})
        res = bool(data.get("result"))
        r = intent.IntentResponse()
        r.async_set_speech(f"{n} is {'a prime' if res else 'not a prime'} number.")
        r.async_set_card("Prime check", f"{n} → {res}")
        return r


class GcdIntent(intent.IntentHandler):
    intent_type = "MathGcd"

    def __init__(self, post: PostFn) -> None:
        self._post = post

    async def async_handle(self, hass: HomeAssistant, intent_obj: intent.Intent) -> intent.IntentResponse:
        a = int(intent_obj.slots["a"]["value"])  # type: ignore[index]
        b = int(intent_obj.slots["b"]["value"])  # type: ignore[index]
        data = await self._post("/algorithms/gcd", {"a": a, "b": b})
        res = data.get("result")
        r = intent.IntentResponse()
        r.async_set_speech(f"The greatest common divisor of {a} and {b} is {res}.")
        r.async_set_card("GCD", f"gcd({a}, {b}) = {res}")
        return r


class LcmIntent(intent.IntentHandler):
    intent_type = "MathLcm"

    def __init__(self, post: PostFn) -> None:
        self._post = post

    async def async_handle(self, hass: HomeAssistant, intent_obj: intent.Intent) -> intent.IntentResponse:
        a = int(intent_obj.slots["a"]["value"])  # type: ignore[index]
        b = int(intent_obj.slots["b"]["value"])  # type: ignore[index]
        data = await self._post("/algorithms/lcm", {"a": a, "b": b})
        res = data.get("result")
        r = intent.IntentResponse()
        r.async_set_speech(f"The least common multiple of {a} and {b} is {res}.")
        r.async_set_card("LCM", f"lcm({a}, {b}) = {res}")
        return r


class PrimeFactorsIntent(intent.IntentHandler):
    intent_type = "MathPrimeFactors"

    def __init__(self, post: PostFn) -> None:
        self._post = post

    async def async_handle(self, hass: HomeAssistant, intent_obj: intent.Intent) -> intent.IntentResponse:
        n = int(intent_obj.slots["n"]["value"])  # type: ignore[index]
        data = await self._post("/algorithms/prime_factors", {"n": n})
        fac = data.get("result", [])
        speak = " × ".join(map(str, fac)) if fac else "none"
        r = intent.IntentResponse()
        r.async_set_speech(f"The prime factors of {n} are {speak}.")
        r.async_set_card("Prime factors", f"{n} → {fac}")
        return r


class MeanIntent(intent.IntentHandler):
    intent_type = "MathMean"

    def __init__(self, post: PostFn) -> None:
        self._post = post

    async def async_handle(self, hass: HomeAssistant, intent_obj: intent.Intent) -> intent.IntentResponse:
        values = _to_floats(intent_obj.slots.get("values", {}).get("value"))
        data = await self._post("/math/mean", {"values": values})
        res = data.get("result")
        r = intent.IntentResponse()
        r.async_set_speech(f"The mean is {res}.")
        r.async_set_card("Mean", f"values={values} → {res}")
        return r


class MedianIntent(intent.IntentHandler):
    intent_type = "MathMedian"

    def __init__(self, post: PostFn) -> None:
        self._post = post

    async def async_handle(self, hass: HomeAssistant, intent_obj: intent.Intent) -> intent.IntentResponse:
        values = _to_floats(intent_obj.slots.get("values", {}).get("value"))
        data = await self._post("/math/median", {"values": values})
        res = data.get("result")
        r = intent.IntentResponse()
        r.async_set_speech(f"The median is {res}.")
        r.async_set_card("Median", f"values={values} → {res}")
        return r


class StdIntent(intent.IntentHandler):
    intent_type = "MathStd"

    def __init__(self, post: PostFn) -> None:
        self._post = post

    async def async_handle(self, hass: HomeAssistant, intent_obj: intent.Intent) -> intent.IntentResponse:
        values = _to_floats(intent_obj.slots.get("values", {}).get("value"))
        sample = bool(intent_obj.slots.get("sample", {}).get("value", False))
        data = await self._post("/math/std", {"values": values, "sample": sample})
        res = data.get("result")
        r = intent.IntentResponse()
        r.async_set_speech(f"The {'sample' if sample else 'population'} standard deviation is {res}.")
        r.async_set_card("Std", f"values={values}, sample={sample} → {res}")
        return r


async def async_register_intents(hass: HomeAssistant, post: PostFn) -> None:
    """Register intent handlers so Assist/LLMs can call them as tools."""
    intent.async_register(hass, AddIntent(post))
    intent.async_register(hass, FibonacciIntent(post))
    intent.async_register(hass, IsPrimeIntent(post))
    intent.async_register(hass, GcdIntent(post))
    intent.async_register(hass, LcmIntent(post))
    intent.async_register(hass, PrimeFactorsIntent(post))
    intent.async_register(hass, MeanIntent(post))
    intent.async_register(hass, MedianIntent(post))
    intent.async_register(hass, StdIntent(post))
