from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol, TypedDict, Union, cast

import httpx

from .models import WeatherSample


class CurrentWeatherPayload(TypedDict):
    """Type definition for the current weather section of the API response."""
    temperature: float
    windspeed: float
    time: str  # ISO8601


class OpenMeteoResponse(TypedDict):
    """Type definition for the complete Open-Meteo API response."""
    latitude: float
    longitude: float
    current_weather: CurrentWeatherPayload


class AsyncWeatherClient(Protocol):
    """Protocol defining the interface for asynchronous weather clients."""
    async def get_current(self, lat: float, lon: float) -> OpenMeteoResponse: ...


ParamsValue = Union[str, float]


@dataclass
class AsyncOpenMeteoClient:
    """
    Asynchronous HTTP client for the Open-Meteo weather API.
    
    Provides typed access to current weather data for specified coordinates.
    """
    base_url: str = "https://api.open-meteo.com/v1/forecast"

    async def get_current(self, lat: float, lon: float) -> OpenMeteoResponse:
        """
        Fetch current weather data for the given coordinates.
        
        Args:
            lat: Latitude of the location
            lon: Longitude of the location
            
        Returns:
            Typed weather data response from the API
            
        Raises:
            httpx.HTTPStatusError: If the API returns a non-2xx status code
        """
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
    """
    Parse an ISO8601 datetime string and ensure it has UTC timezone.
    
    If the input has no timezone info, UTC is assumed.
    """
    d = datetime.fromisoformat(dt)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d


def store_sample_from_payload(
    payload: OpenMeteoResponse,
    city: str,
) -> WeatherSample:
    """
    Create and persist a WeatherSample from an API response.
    
    Args:
        payload: The weather data from the API
        city: Name of the city for this sample
        
    Returns:
        The created WeatherSample instance
    """
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
