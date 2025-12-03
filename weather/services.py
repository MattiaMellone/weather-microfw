# weather/services.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol, TypedDict, Union, cast

import httpx

from .models import WeatherSample


class CurrentWeatherPayload(TypedDict):
    temperature: float
    windspeed: float
    time: str  # ISO8601


class OpenMeteoResponse(TypedDict):
    latitude: float
    longitude: float
    current_weather: CurrentWeatherPayload


class AsyncWeatherClient(Protocol):
    async def get_current(self, lat: float, lon: float) -> OpenMeteoResponse: ...


ParamsValue = Union[str, float]


@dataclass
class AsyncOpenMeteoClient:
    base_url: str = "https://api.open-meteo.com/v1/forecast"

    async def get_current(self, lat: float, lon: float) -> OpenMeteoResponse:
        params: dict[str, ParamsValue] = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(self.base_url, params=params)
            r.raise_for_status()
        data = cast(OpenMeteoResponse, r.json())
        return data


def _parse_iso8601(dt: str) -> datetime:
    d = datetime.fromisoformat(dt)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d


def store_sample_from_payload(
    payload: OpenMeteoResponse,
    city: str,
) -> WeatherSample:
    cw = payload["current_weather"]

    sample = WeatherSample.objects.create(
        city=city,
        latitude=payload["latitude"],
        longitude=payload["longitude"],
        temperature_c=cw["temperature"],
        windspeed_kmh=cw["windspeed"],
        observed_at=_parse_iso8601(cw["time"]),
    )
    return sample
