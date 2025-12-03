from __future__ import annotations

import asyncio

from celery import shared_task

from .services import AsyncOpenMeteoClient, store_sample_from_payload


@shared_task
def fetch_weather_task(city: str, lat: float, lon: float) -> None:
    """
    Celery task that fetches weather data and stores it in the database.
    
    Uses an async HTTP client to call the weather API, then stores the result
    in a fully synchronous database context to avoid ORM compatibility issues.
    """
    client = AsyncOpenMeteoClient()

    payload = asyncio.run(client.get_current(lat=lat, lon=lon))
    store_sample_from_payload(payload, city)
