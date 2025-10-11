import os
import json
from unittest.mock import patch
import pytest

from app import app, get_hakata_weather_text


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
