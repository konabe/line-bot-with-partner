import pytest
import requests

from src.infrastructure.adapters.weather_adapter import WeatherAdapter
from src.infrastructure.logger import Logger


class FakeResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}

    def raise_for_status(self):
        if 400 <= self.status_code:
            raise requests.exceptions.HTTPError(response=self)  # type: ignore

    def json(self):
        return self._json


class MockLogger:
    """テスト用のモックロガー"""

    def __init__(self):
        self.logs = []

    def info(self, message):
        self.logs.append(("INFO", message))

    def error(self, message):
        self.logs.append(("ERROR", message))

    def warning(self, message):
        self.logs.append(("WARNING", message))

    def debug(self, message):
        self.logs.append(("DEBUG", message))


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


def test_initialization_with_custom_logger(monkeypatch):
    """カスタムロガーを渡して初期化できることを確認"""
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "test_key")
    mock_logger = MockLogger()
    adapter = WeatherAdapter(logger=mock_logger)
    assert adapter.logger is mock_logger


def test_initialization_without_logger(monkeypatch):
    """ロガーなしで初期化した場合、デフォルトロガーが使用される"""
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "test_key")
    adapter = WeatherAdapter()
    assert adapter.logger is not None
    assert hasattr(adapter.logger, "info")
    assert hasattr(adapter.logger, "error")


def test_api_key_is_set_correctly(monkeypatch):
    """環境変数からAPIキーが正しく設定される"""
    test_key = "test_api_key_12345"
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", test_key)
    adapter = WeatherAdapter()
    assert adapter.api_key == test_key


def test_base_url_is_correct():
    """ベースURLが正しく設定される"""
    adapter = WeatherAdapter()
    assert adapter.base_url == "https://api.openweathermap.org/data/2.5/weather"


def test_success_response_with_proper_formatting(monkeypatch):
    """成功レスポンスが正しくフォーマットされる"""
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "dummy")

    json_data = {
        "weather": [{"description": "曇りがち"}],
        "main": {"temp": 15.7, "feels_like": 14.3, "humidity": 75},
    }

    def fake_get(url, params=None, timeout=None):
        return FakeResponse(status_code=200, json_data=json_data)

    monkeypatch.setattr("requests.get", fake_get)
    adapter = WeatherAdapter()
    res = adapter.get_weather_text("Osaka")

    assert "Osaka" in res
    assert "曇りがち" in res
    assert "16℃" in res  # 15.7を四捨五入
    assert "14℃" in res  # 14.3を四捨五入
    assert "75%" in res


def test_request_params_are_correct(monkeypatch):
    """APIリクエストのパラメータが正しい"""
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "test_key")

    captured_params = {}

    json_data = {
        "weather": [{"description": "晴れ"}],
        "main": {"temp": 20.0, "feels_like": 19.0, "humidity": 60},
    }

    def fake_get(url, params=None, timeout=None):
        captured_params.update(params or {})
        return FakeResponse(status_code=200, json_data=json_data)

    monkeypatch.setattr("requests.get", fake_get)
    adapter = WeatherAdapter()
    adapter.get_weather_text("Fukuoka")

    assert captured_params["q"] == "Fukuoka,JP"
    assert captured_params["appid"] == "test_key"
    assert captured_params["units"] == "metric"
    assert captured_params["lang"] == "ja"


def test_timeout_is_set(monkeypatch):
    """リクエストにタイムアウトが設定される"""
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "test_key")

    captured_timeout = None

    json_data = {
        "weather": [{"description": "晴れ"}],
        "main": {"temp": 20.0, "feels_like": 19.0, "humidity": 60},
    }

    def fake_get(url, params=None, timeout=None):
        nonlocal captured_timeout
        captured_timeout = timeout
        return FakeResponse(status_code=200, json_data=json_data)

    monkeypatch.setattr("requests.get", fake_get)
    adapter = WeatherAdapter()
    adapter.get_weather_text("Tokyo")

    assert captured_timeout == 10


def test_http_error_500(monkeypatch):
    """HTTP 500エラーの処理"""
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "test_key")

    def fake_get(url, params=None, timeout=None):
        return FakeResponse(status_code=500)

    monkeypatch.setattr("requests.get", fake_get)
    adapter = WeatherAdapter()
    res = adapter.get_weather_text("Tokyo")

    assert "取得に失敗" in res or "ネットワークエラー" in res


def test_connection_timeout(monkeypatch):
    """接続タイムアウトの処理"""
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "test_key")

    def fake_get(url, params=None, timeout=None):
        raise requests.exceptions.Timeout("Connection timeout")

    monkeypatch.setattr("requests.get", fake_get)
    adapter = WeatherAdapter()
    res = adapter.get_weather_text("Tokyo")

    assert "取得に失敗" in res or "ネットワークエラー" in res


def test_unexpected_exception(monkeypatch):
    """予期しない例外の処理"""
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "test_key")

    def fake_get(url, params=None, timeout=None):
        raise ValueError("Unexpected error")

    monkeypatch.setattr("requests.get", fake_get)
    adapter = WeatherAdapter()
    res = adapter.get_weather_text("Tokyo")

    assert "予期しないエラー" in res


def test_logging_on_no_api_key(monkeypatch):
    """APIキーなしの場合にログが記録される"""
    monkeypatch.delenv("OPENWEATHERMAP_API_KEY", raising=False)
    mock_logger = MockLogger()
    adapter = WeatherAdapter(logger=mock_logger)
    adapter.get_weather_text("Tokyo")

    error_logs = [log for log in mock_logger.logs if log[0] == "ERROR"]
    assert len(error_logs) > 0
    assert any("OPENWEATHERMAP_API_KEY" in log[1] for log in error_logs)


def test_logging_on_404(monkeypatch):
    """404エラーの場合にログが記録される"""
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "test_key")
    mock_logger = MockLogger()

    def fake_get(url, params=None, timeout=None):
        return FakeResponse(status_code=404)

    monkeypatch.setattr("requests.get", fake_get)
    adapter = WeatherAdapter(logger=mock_logger)
    adapter.get_weather_text("NoSuchCity")

    info_logs = [log for log in mock_logger.logs if log[0] == "INFO"]
    assert len(info_logs) > 0
    assert any("location not found" in log[1] for log in info_logs)


def test_logging_on_network_error(monkeypatch):
    """ネットワークエラー時にログが記録される"""
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "test_key")
    mock_logger = MockLogger()

    def fake_get(url, params=None, timeout=None):
        raise requests.exceptions.RequestException("Network error")

    monkeypatch.setattr("requests.get", fake_get)
    adapter = WeatherAdapter(logger=mock_logger)
    adapter.get_weather_text("Tokyo")

    error_logs = [log for log in mock_logger.logs if log[0] == "ERROR"]
    assert len(error_logs) > 0
    assert any("API request failed" in log[1] for log in error_logs)


def test_temperature_rounding(monkeypatch):
    """温度が正しく四捨五入される"""
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "test_key")

    json_data = {
        "weather": [{"description": "雨"}],
        "main": {"temp": 18.4, "feels_like": 17.6, "humidity": 80},
    }

    def fake_get(url, params=None, timeout=None):
        return FakeResponse(status_code=200, json_data=json_data)

    monkeypatch.setattr("requests.get", fake_get)
    adapter = WeatherAdapter()
    res = adapter.get_weather_text("Sapporo")

    assert "18℃" in res  # 18.4を四捨五入
    assert "18℃" in res  # 17.6を四捨五入


def test_extreme_temperature_values(monkeypatch):
    """極端な温度値の処理"""
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "test_key")

    json_data = {
        "weather": [{"description": "猛暑"}],
        "main": {"temp": 38.9, "feels_like": 42.1, "humidity": 30},
    }

    def fake_get(url, params=None, timeout=None):
        return FakeResponse(status_code=200, json_data=json_data)

    monkeypatch.setattr("requests.get", fake_get)
    adapter = WeatherAdapter()
    res = adapter.get_weather_text("Tokyo")

    assert "39℃" in res
    assert "42℃" in res
    assert "30%" in res
