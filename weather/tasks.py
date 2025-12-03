from __future__ import annotations

from celery import shared_task

from .services import OpenMeteoClient, fetch_and_store


@shared_task
def fetch_weather_task(city: str, lat: float, lon: float) -> None:
    client = OpenMeteoClient()
    fetch_and_store(client, city, lat, lon)
