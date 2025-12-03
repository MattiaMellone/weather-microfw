"""
Unit tests for the weather application.

Tests cover the weather API endpoints, service layer, and Celery tasks.
"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from django.test import TestCase

from .models import WeatherSample
from .services import (
    AsyncOpenMeteoClient,
    OpenMeteoResponse,
    _parse_iso8601,
    store_sample_from_payload,
)


class ParseISO8601Tests(TestCase):
    """Tests for the _parse_iso8601 function."""

    def test_parse_iso8601_with_utc_timezone(self) -> None:
        """Test parsing ISO8601 datetime with UTC timezone."""
        dt_str = "2025-12-03T12:00:00+00:00"
        result = _parse_iso8601(dt_str)
        
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 3
        assert result.hour == 12
        assert result.minute == 0
        assert result.second == 0
        assert result.tzinfo == timezone.utc

    def test_parse_iso8601_without_timezone(self) -> None:
        """Test parsing ISO8601 datetime without timezone (assumes UTC)."""
        dt_str = "2025-12-03T12:00:00"
        result = _parse_iso8601(dt_str)
        
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 3
        assert result.hour == 12
        assert result.minute == 0
        assert result.second == 0
        assert result.tzinfo == timezone.utc

    def test_parse_iso8601_with_different_timezone(self) -> None:
        """Test parsing ISO8601 datetime with non-UTC timezone."""
        dt_str = "2025-12-03T12:00:00+02:00"
        result = _parse_iso8601(dt_str)
        
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 3
        # Timezone should be preserved
        assert result.tzinfo is not None


class StoreSampleFromPayloadTests(TestCase):
    """Tests for the store_sample_from_payload function."""

    def test_store_sample_from_payload_creates_weather_sample(self) -> None:
        """Test that a weather sample is created from API payload."""
        payload: OpenMeteoResponse = {
            "latitude": 41.12,
            "longitude": 16.87,
            "current_weather": {
                "temperature": 15.5,
                "windspeed": 12.3,
                "time": "2025-12-03T12:00:00",
            },
        }
        
        sample = store_sample_from_payload(payload, "Bari")
        
        assert sample.city == "Bari"
        assert sample.latitude == 41.12
        assert sample.longitude == 16.87
        assert sample.temperature_c == 15.5
        assert sample.windspeed_kmh == 12.3
        assert sample.observed_at.year == 2025
        assert sample.observed_at.month == 12
        assert sample.observed_at.day == 3

    def test_store_sample_persisted_to_database(self) -> None:
        """Test that the weather sample is persisted to the database."""
        payload: OpenMeteoResponse = {
            "latitude": 40.85,
            "longitude": 14.27,
            "current_weather": {
                "temperature": 18.0,
                "windspeed": 10.5,
                "time": "2025-12-03T14:30:00",
            },
        }
        
        store_sample_from_payload(payload, "Naples")
        
        # Verify it's in the database
        sample = WeatherSample.objects.get(city="Naples")
        assert sample.latitude == 40.85
        assert sample.longitude == 14.27
        assert sample.temperature_c == 18.0


@pytest.mark.asyncio
class AsyncOpenMeteoClientTests:
    """Tests for the AsyncOpenMeteoClient class."""

    async def test_get_current_success(self) -> None:
        """Test successful weather data retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "latitude": 41.12,
            "longitude": 16.87,
            "current_weather": {
                "temperature": 15.5,
                "windspeed": 12.3,
                "time": "2025-12-03T12:00:00",
            },
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            client = AsyncOpenMeteoClient()
            result = await client.get_current(lat=41.12, lon=16.87)
            
            assert result["latitude"] == 41.12
            assert result["longitude"] == 16.87
            assert result["current_weather"]["temperature"] == 15.5
            assert result["current_weather"]["windspeed"] == 12.3

    async def test_get_current_with_custom_base_url(self) -> None:
        """Test that custom base URL is used."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "latitude": 41.12,
            "longitude": 16.87,
            "current_weather": {
                "temperature": 15.5,
                "windspeed": 12.3,
                "time": "2025-12-03T12:00:00",
            },
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            custom_url = "https://custom-api.example.com/forecast"
            client = AsyncOpenMeteoClient(base_url=custom_url)
            await client.get_current(lat=41.12, lon=16.87)
            
            # Verify the custom URL was used
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[0][0] == custom_url

    async def test_get_current_raises_for_http_error(self) -> None:
        """Test that HTTP errors are properly raised."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found",
            request=MagicMock(),
            response=MagicMock(),
        )
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            client = AsyncOpenMeteoClient()
            
            with pytest.raises(httpx.HTTPStatusError):
                await client.get_current(lat=41.12, lon=16.87)


class WeatherSampleModelTests(TestCase):
    """Tests for the WeatherSample model."""

    def test_str_representation(self) -> None:
        """Test the string representation of WeatherSample."""
        sample = WeatherSample.objects.create(
            city="Rome",
            latitude=41.9,
            longitude=12.5,
            temperature_c=20.0,
            windspeed_kmh=5.0,
            observed_at=datetime(2025, 12, 3, 12, 0, 0, tzinfo=timezone.utc),
        )
        
        expected = "Rome @ 2025-12-03 12:00:00+00:00: 20.0°C"
        assert str(sample) == expected

    def test_default_ordering(self) -> None:
        """Test that samples are ordered by observed_at descending."""
        WeatherSample.objects.create(
            city="Test1",
            latitude=41.0,
            longitude=16.0,
            temperature_c=10.0,
            windspeed_kmh=5.0,
            observed_at=datetime(2025, 12, 1, 12, 0, 0, tzinfo=timezone.utc),
        )
        WeatherSample.objects.create(
            city="Test2",
            latitude=41.0,
            longitude=16.0,
            temperature_c=15.0,
            windspeed_kmh=8.0,
            observed_at=datetime(2025, 12, 3, 12, 0, 0, tzinfo=timezone.utc),
        )
        WeatherSample.objects.create(
            city="Test3",
            latitude=41.0,
            longitude=16.0,
            temperature_c=12.0,
            windspeed_kmh=6.0,
            observed_at=datetime(2025, 12, 2, 12, 0, 0, tzinfo=timezone.utc),
        )
        
        samples = list(WeatherSample.objects.all())
        assert samples[0].city == "Test2"  # Most recent
        assert samples[1].city == "Test3"
        assert samples[2].city == "Test1"  # Oldest


class EnqueueWeatherFetchViewTests(TestCase):
    """Tests for the enqueue_weather_fetch view."""

    @patch("weather.views.fetch_weather_task")
    def test_enqueue_weather_fetch_with_params(self, mock_task: MagicMock) -> None:
        """Test that weather fetch is enqueued with provided parameters."""
        response = self.client.get(
            "/weather/fetch/?city=Milan&lat=45.46&lon=9.19"
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["detail"] == "Fetch scheduled"
        assert data["city"] == "Milan"
        assert data["lat"] == 45.46
        assert data["lon"] == 9.19
        
        mock_task.delay.assert_called_once_with("Milan", 45.46, 9.19)

    @patch("weather.views.fetch_weather_task")
    def test_enqueue_weather_fetch_with_default_params(
        self, mock_task: MagicMock
    ) -> None:
        """Test that weather fetch uses default parameters when none provided."""
        response = self.client.get("/weather/fetch/")
        
        assert response.status_code == 202
        data = response.json()
        assert data["detail"] == "Fetch scheduled"
        assert data["city"] == "Bari"
        assert data["lat"] == 41.12
        assert data["lon"] == 16.87
        
        mock_task.delay.assert_called_once_with("Bari", 41.12, 16.87)


class LatestWeatherViewTests(TestCase):
    """Tests for the latest_weather view."""

    def test_latest_weather_with_no_samples(self) -> None:
        """Test response when no weather samples exist."""
        response = self.client.get("/weather/latest/")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "No samples yet"

    def test_latest_weather_returns_most_recent_sample(self) -> None:
        """Test that the most recent sample is returned."""
        # Create older sample
        WeatherSample.objects.create(
            city="Older",
            latitude=41.0,
            longitude=16.0,
            temperature_c=10.0,
            windspeed_kmh=5.0,
            observed_at=datetime(2025, 12, 1, 12, 0, 0, tzinfo=timezone.utc),
        )
        
        # Create newest sample
        newest = WeatherSample.objects.create(
            city="Newest",
            latitude=42.0,
            longitude=17.0,
            temperature_c=20.0,
            windspeed_kmh=10.0,
            observed_at=datetime(2025, 12, 3, 12, 0, 0, tzinfo=timezone.utc),
        )
        
        response = self.client.get("/weather/latest/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["city"] == "Newest"
        assert data["lat"] == 42.0
        assert data["lon"] == 17.0
        assert data["temp"] == 20.0
        assert data["wind"] == 10.0
        assert "observed" in data
        assert "created_at" in data
