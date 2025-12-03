from __future__ import annotations

from django.http import HttpRequest, JsonResponse

from .tasks import fetch_weather_task
from .models import WeatherSample


def enqueue_weather_fetch(request: HttpRequest) -> JsonResponse:
    """
    Enqueue an asynchronous weather fetch task for the specified location.
    
    Returns HTTP 202 to indicate the fetch has been scheduled for background processing.
    """
    city = request.GET.get("city", "Bari")
    lat_str = request.GET.get("lat", "41.12")
    lon_str = request.GET.get("lon", "16.87")

    lat = float(lat_str)
    lon = float(lon_str)

    # Schedule the async weather fetch task
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
    """
    Retrieve the most recent weather sample from the database.
    
    Returns HTTP 404 if no samples exist, otherwise returns the latest observation.
    """
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
