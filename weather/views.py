# weather/views.py
from __future__ import annotations

from django.http import HttpRequest, JsonResponse

from .tasks import fetch_weather_task
from .models import WeatherSample


def enqueue_weather_fetch(request: HttpRequest) -> JsonResponse:
    city = request.GET.get("city", "Bari")
    lat_str = request.GET.get("lat", "41.12")
    lon_str = request.GET.get("lon", "16.87")

    lat = float(lat_str)
    lon = float(lon_str)

    # metto in coda il job async
    fetch_weather_task.delay(city, lat, lon)

    return JsonResponse(
        {
            "detail": "Fetch scheduled",
            "city": city,
            "lat": lat,
            "lon": lon,
        },
        status=202,
    )


def latest_weather(request: HttpRequest) -> JsonResponse:
    sample = WeatherSample.objects.order_by("-observed_at").first()
    if sample is None:
        return JsonResponse({"detail": "No samples yet"}, status=404)

    return JsonResponse(
        {
            "city": sample.city,
            "lat": sample.latitude,
            "lon": sample.longitude,
            "temp": sample.temperature_c,
            "wind": sample.windspeed_kmh,
            "observed": sample.observed_at.isoformat(),
            "created_at": sample.created_at.isoformat(),
        }
    )
