import os
import json
from unittest.mock import patch
import pytest

from app import (
    app,
    get_hakata_weather_text,
    extract_location_from_weather_query,
    geocode_location,
    get_location_weather_text,
)


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health(client):
    resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.data == b'ok'


def test_get_hakata_weather_text_success(monkeypatch):
    class DummyResp:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                'current': {
                    'temperature_2m': 25.1,
                    'wind_speed_10m': 2.5,
                    'weather_code': 63,
                }
            }

    with patch('app.requests.get', return_value=DummyResp()):
        text = get_hakata_weather_text()
        assert '博多の現在の天気' in text
        assert '25.1' in text


def test_get_hakata_weather_text_failure(monkeypatch):
    class DummyResp:
        def raise_for_status(self):
            raise Exception('error')

    with patch('app.requests.get', return_value=DummyResp()):
        text = get_hakata_weather_text()
        assert '取得できません' in text


def test_extract_location_from_weather_query():
    assert extract_location_from_weather_query('東京の天気') == '東京'
    assert extract_location_from_weather_query('大阪の天気です') == '大阪'
    assert extract_location_from_weather_query('天気') is None


def test_get_location_weather_text_success(monkeypatch):
    # geocode -> weather の2段階呼び出しを順番にモック
    class GeoResp:
        status_code = 200
        def raise_for_status(self):
            return None
        def json(self):
            return { 'results': [{ 'latitude': 35.0, 'longitude': 135.0, 'name': 'テスト市' }] }

    class WeatherResp:
        status_code = 200
        def raise_for_status(self):
            return None
        def json(self):
            return { 'current': { 'temperature_2m': 20.0, 'wind_speed_10m': 1.2, 'weather_code': 0 } }

    def fake_get(url, timeout=5):
        if 'geocoding-api' in url:
            return GeoResp()
        return WeatherResp()

    with patch('app.requests.get', side_effect=fake_get):
        text = get_location_weather_text('どこか')
        assert 'テスト市の現在の天気' in text
        assert '20.0' in text


def test_get_location_weather_text_geocode_fail(monkeypatch):
    class GeoResp:
        status_code = 200
        def raise_for_status(self):
            return None
        def json(self):
            return { 'results': [] }

    with patch('app.requests.get', return_value=GeoResp()):
        text = get_location_weather_text('未知都市')
        assert '見つけられません' in text


def test_get_location_weather_text_weather_fail(monkeypatch):
    # geocode OK -> weather fail
    class GeoResp:
        status_code = 200
        def raise_for_status(self):
            return None
        def json(self):
            return { 'results': [{ 'latitude': 35.0, 'longitude': 140.0, 'name': 'X市' }] }

    class WeatherResp:
        def raise_for_status(self):
            raise Exception('error')

    def fake_get(url, timeout=5):
        if 'geocoding-api' in url:
            return GeoResp()
        return WeatherResp()

    with patch('app.requests.get', side_effect=fake_get):
        text = get_location_weather_text('X市')
        assert '取得できません' in text or 'できません' in text
