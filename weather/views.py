from typing import Any
from django.http import HttpRequest, JsonResponse
from .models import WeatherSample
from .services import OpenMeteoClient, fetch_and_store

client = OpenMeteoClient()


def fetch_weather(request: HttpRequest) -> JsonResponse:
    city = request.GET.get("city", "Unknown")
    lat_str = request.GET.get("lat", "41.12")
    lon_str = request.GET.get("lon", "16.87")

    lat = float(lat_str)
    lon = float(lon_str)

    sample = fetch_and_store(client, city, lat, lon)

    return JsonResponse(
        {
            "city": sample.city,
            "lat": sample.latitude,
            "lon": sample.longitude,
            "temp": sample.temperature_c,
            "wind": sample.windspeed_kmh,
            "observed": sample.observed_at.isoformat(),
        }
    )


def latest_weather(request: HttpRequest) -> JsonResponse:
    """
    GET /weather/latest/
    Ritorna l'ultimo sample in DB (qualsiasi città).
    """
    sample = WeatherSample.objects.order_by("-observed_at").first()
    if sample is None:
        return JsonResponse({"detail": "No samples yet"}, status=404)

    payload: dict[str, Any] = {
        "city": sample.city,
        "lat": sample.latitude,
        "lon": sample.longitude,
        "temp": sample.temperature_c,
        "wind": sample.windspeed_kmh,
        "observed": sample.observed_at.isoformat(),
        "created_at": sample.created_at.isoformat(),
    }
    return JsonResponse(payload)
