# Math Tools (Home Assistant custom integration)

Exposes math & algorithm services (and Assist intents) that proxy to a FastAPI server.
Services: add, subtract, multiply, divide, power, mean, median, std, gcd, lcm,
is_prime, prime_factors, fibonacci, sort, moving_average, rolling_min, rolling_max.

## Installation (HACS - Custom repository)
1. HACS → Integrations → ⋮ → Custom repositories
2. URL: https://github.com/<you>/math_tools-hacs  |  Category: Integration
3. Add → then find “Math Tools” in HACS and Install → Restart HA.

## Configure the FastAPI server URL
Set environment variables on the HA host/container:
- `MATH_TOOLS_BASE_URL` (e.g. `http://172.16.2.223:8111`)
- `MATH_TOOLS_API_KEY` (optional)

## Test a service
Developer Tools → Services → `math_tools.fibonacci`, data:
```json
{ "n": 10 }
