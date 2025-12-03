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


class WeatherClient(Protocol):
    def get_current(self, lat: float, lon: float) -> OpenMeteoResponse: ...


ParamsValue = Union[str, float]


@dataclass
class OpenMeteoClient:
    base_url: str = "https://api.open-meteo.com/v1/forecast"

    def get_current(self, lat: float, lon: float) -> OpenMeteoResponse:
        params: dict[str, ParamsValue] = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true",
        }
        with httpx.Client(timeout=10.0) as client:
            r = client.get(self.base_url, params=params)
            r.raise_for_status()
        data = cast(OpenMeteoResponse, r.json())
        return data


def parse_iso8601(dt: str) -> datetime:
    d = datetime.fromisoformat(dt)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d


def fetch_and_store(
    client: WeatherClient,
    city: str,
    lat: float,
    lon: float,
) -> WeatherSample:
    data = client.get_current(lat=lat, lon=lon)
    cw = data["current_weather"]

    sample = WeatherSample.objects.create(
        city=city,
        latitude=data["latitude"],
        longitude=data["longitude"],
        temperature_c=cw["temperature"],
        windspeed_kmh=cw["windspeed"],
        observed_at=parse_iso8601(cw["time"]),
    )
    return sample
