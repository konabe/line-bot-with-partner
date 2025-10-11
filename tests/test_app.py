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
    detect_janken_hand,
    play_janken,
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


# ---- Janken (Rock-Paper-Scissors) Tests -----------------------------------


def test_detect_janken_hand_emoji():
    """絵文字でのじゃんけん手の検出"""
    assert detect_janken_hand('✊') == 'rock'
    assert detect_janken_hand('✋') == 'paper'
    assert detect_janken_hand('✌') == 'scissors'
    assert detect_janken_hand('✌️') == 'scissors'


def test_detect_janken_hand_japanese():
    """日本語でのじゃんけん手の検出"""
    assert detect_janken_hand('グー') == 'rock'
    assert detect_janken_hand('ぐー') == 'rock'
    assert detect_janken_hand('パー') == 'paper'
    assert detect_janken_hand('ぱー') == 'paper'
    assert detect_janken_hand('チョキ') == 'scissors'
    assert detect_janken_hand('ちょき') == 'scissors'


def test_detect_janken_hand_mixed():
    """絵文字と日本語が混在している場合"""
    assert detect_janken_hand('✊ グー') == 'rock'
    assert detect_janken_hand('じゃんけん ✋') == 'paper'
    assert detect_janken_hand('✌️でいくよ') == 'scissors'


def test_detect_janken_hand_none():
    """じゃんけんの手が検出されない場合"""
    assert detect_janken_hand('こんにちは') is None
    assert detect_janken_hand('天気') is None
    assert detect_janken_hand('') is None


def test_play_janken_returns_none_for_non_janken():
    """じゃんけんでないテキストの場合はNoneを返す"""
    assert play_janken('こんにちは') is None
    assert play_janken('東京の天気') is None


def test_play_janken_returns_result():
    """じゃんけんの結果が返される"""
    result = play_janken('✊')
    assert result is not None
    assert 'あなた:' in result
    assert 'Bot:' in result
    assert ('あいこ' in result or 'あなたの勝ち！' in result or 'あなたの負け...' in result)


def test_play_janken_contains_emojis():
    """結果に絵文字が含まれている"""
    result = play_janken('グー')
    assert result is not None
    # 結果に絵文字が含まれている
    assert '✊' in result or '✋' in result or '✌️' in result


def test_play_janken_deterministic_with_seed(monkeypatch):
    """ランダム性をモックして勝敗を確認"""
    # ボットが常にrock(✊)を出すようにモック
    with patch('app.random.choice', return_value='rock'):
        # ユーザーがrock -> あいこ
        result = play_janken('✊')
        assert 'あいこ' in result
        
        # ユーザーがpaper -> 勝ち
        result = play_janken('✋')
        assert 'あなたの勝ち！' in result
        
        # ユーザーがscissors -> 負け
        result = play_janken('✌️')
        assert 'あなたの負け...' in result
