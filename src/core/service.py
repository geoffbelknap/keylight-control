from __future__ import annotations

import logging
import asyncio

import aiohttp

from .models import KeyLight

logger = logging.getLogger(__name__)


class DeviceCommunicationError(RuntimeError):
    """A device could not be reached or returned an invalid response."""


class KeyLightService:
    """HTTP service; callers receive failures instead of assuming success."""

    def __init__(self, timeout_seconds: float = 2.0) -> None:
        self._timeout = timeout_seconds

    async def _request(self, keylight: KeyLight, method: str, data=None) -> dict:
        host = f"[{keylight.ip}]" if ":" in keylight.ip else keylight.ip
        url = f"http://{host}:{keylight.port}/elgato/lights"
        try:
            timeout = aiohttp.ClientTimeout(total=self._timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.request(method, url, json=data) as response:
                    response.raise_for_status()
                    if method == "PUT":
                        return {}
                    result = await response.json()
                    light = result["lights"][0]
                    if (light["on"] not in (0, 1) or
                            not 0 <= int(light["brightness"]) <= 100 or
                            not 143 <= int(light["temperature"]) <= 344):
                        raise ValueError("Invalid light state")
                    return result
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, KeyError, IndexError, TypeError) as exc:
            reason = str(exc) or type(exc).__name__
            message = f"{method} {keylight.name} ({keylight.ip}): {reason}"
            logger.warning(message)
            raise DeviceCommunicationError(message) from exc

    async def set_light_state(self, keylight: KeyLight, changes=None) -> dict:
        if changes is None:
            changes = {"on": int(keylight.on), "brightness": keylight.brightness,
                       "temperature": keylight.temperature}
        actual = await self.fetch_light_state(keylight)
        desired = dict(actual["lights"][0])
        desired.update(changes)
        data = {"numberOfLights": 1, "lights": [{
            "on": int(desired["on"]), "brightness": desired["brightness"],
            "temperature": desired["temperature"],
        }]}
        await self._request(keylight, "PUT", data)
        # Read back the device rather than presenting the requested state as fact.
        return await self.fetch_light_state(keylight)

    async def fetch_light_state(self, keylight: KeyLight) -> dict:
        return await self._request(keylight, "GET")
