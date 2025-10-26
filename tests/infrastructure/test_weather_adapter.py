import requests
import os

from src.infrastructure.weather_adapter import WeatherAdapter


class FakeResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}

    def raise_for_status(self):
        if 400 <= self.status_code:
            raise requests.exceptions.HTTPError(response=self)

    def json(self):
        return self._json


def test_no_api_key(monkeypatch):
    # ensure env var is absent
    monkeypatch.delenv("OPENWEATHERMAP_API_KEY", raising=False)
    adapter = WeatherAdapter()
    res = adapter.get_weather_text("Tokyo")
    assert "API設定" in res or "取得に失敗" in res


def test_404_location_not_found(monkeypatch):
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "dummy")

    def fake_get(url, params=None, timeout=None):
        return FakeResponse(status_code=404)

    monkeypatch.setattr("requests.get", fake_get)
    adapter = WeatherAdapter()
    res = adapter.get_weather_text("NoSuchCity")
    assert "見つかりませんでした" in res


def test_success_response(monkeypatch):
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "dummy")

    json_data = {
        "weather": [{"description": "晴れ"}],
        "main": {"temp": 20.5, "feels_like": 19.2, "humidity": 60},
    }

    def fake_get(url, params=None, timeout=None):
        return FakeResponse(status_code=200, json_data=json_data)

    monkeypatch.setattr("requests.get", fake_get)
    adapter = WeatherAdapter()
    res = adapter.get_weather_text("Tokyo")
    assert "晴れ" in res
    assert "気温" in res and "湿度" in res


def test_network_error(monkeypatch):
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "dummy")

    def fake_get(url, params=None, timeout=None):
        raise requests.exceptions.RequestException("network down")

    monkeypatch.setattr("requests.get", fake_get)
    adapter = WeatherAdapter()
    res = adapter.get_weather_text("Tokyo")
    assert "ネットワークエラー" in res or "取得に失敗" in res


def test_parse_error_returns_message(monkeypatch):
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "dummy")

    # json missing expected keys -> KeyError path
    def fake_get(url, params=None, timeout=None):
        return FakeResponse(status_code=200, json_data={})

    monkeypatch.setattr("requests.get", fake_get)
    adapter = WeatherAdapter()
    res = adapter.get_weather_text("Tokyo")
    assert "解析に失敗" in res or "解析" in res
