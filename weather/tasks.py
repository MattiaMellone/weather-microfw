from __future__ import annotations

import asyncio

from celery import shared_task

from .services import AsyncOpenMeteoClient, store_sample_from_payload


@shared_task
def fetch_weather_task(city: str, lat: float, lon: float) -> None:
    """
    Task Celery:
    - usa un client async per chiamare l'API meteo
    - salva i dati su DB in contesto completamente sync
    """
    client = AsyncOpenMeteoClient()

    payload = asyncio.run(client.get_current(lat=lat, lon=lon))
    store_sample_from_payload(payload, city)
