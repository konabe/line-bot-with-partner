from unittest.mock import MagicMock

from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

from src.application.usecases.send_weather_usecase import SendWeatherUsecase
from tests.support.mock_adapter import MockMessagingAdapter


class FakeEvent:
    def __init__(self):
        self.reply_token = "test_reply_token_123"


def test_execute_with_simple_weather_query(monkeypatch):
    """シンプルな「天気」クエリでデフォルト都市の天気が返される結合テスト"""
    monkeypatch.setenv("WEATHER_LOCATIONS", "東京,大阪")

    mock_line_adapter = MockMessagingAdapter()
    mock_weather_adapter = MagicMock()
    mock_weather_adapter.get_weather_text.side_effect = lambda city: f"{city}の天気: 晴れ"

    usecase = SendWeatherUsecase(mock_line_adapter, mock_weather_adapter)
    event = FakeEvent()

    usecase.execute(event, "天気")

    assert mock_weather_adapter.get_weather_text.call_count == 2
    mock_weather_adapter.get_weather_text.assert_any_call("東京")
    mock_weather_adapter.get_weather_text.assert_any_call("大阪")

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    assert isinstance(reply, ReplyMessageRequest)
    assert reply.reply_token == "test_reply_token_123"
    assert len(reply.messages) == 1
    assert isinstance(reply.messages[0], TextMessage)
    assert "東京の天気: 晴れ" in reply.messages[0].text
    assert "大阪の天気: 晴れ" in reply.messages[0].text


def test_execute_with_specific_city_query():
    """特定の都市名を含むクエリで該当都市の天気が返される結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_weather_adapter = MagicMock()
    mock_weather_adapter.get_weather_text.return_value = "福岡の天気: 曇り"

    usecase = SendWeatherUsecase(mock_line_adapter, mock_weather_adapter)
    event = FakeEvent()

    usecase.execute(event, "福岡の天気")

    mock_weather_adapter.get_weather_text.assert_called_once_with("福岡")

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    assert isinstance(reply.messages[0], TextMessage)
    assert "福岡の天気: 曇り" in reply.messages[0].text


def test_execute_with_no_city_pattern_match():
    """都市名パターンにマッチしない場合は抽出された文字列を検索する結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_weather_adapter = MagicMock()
    mock_weather_adapter.get_weather_text.return_value = "今日の天気: 晴れ"

    usecase = SendWeatherUsecase(mock_line_adapter, mock_weather_adapter)
    event = FakeEvent()

    usecase.execute(event, "今日の天気は？")

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    assert isinstance(reply.messages[0], TextMessage)


def test_execute_without_weather_locations_env(monkeypatch):
    """WEATHER_LOCATIONS環境変数が未設定の場合のエラーメッセージ結合テスト"""
    monkeypatch.delenv("WEATHER_LOCATIONS", raising=False)

    mock_line_adapter = MockMessagingAdapter()
    mock_weather_adapter = MagicMock()

    usecase = SendWeatherUsecase(mock_line_adapter, mock_weather_adapter)
    event = FakeEvent()

    usecase.execute(event, "天気")

    mock_weather_adapter.get_weather_text.assert_not_called()

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    assert isinstance(reply.messages[0], TextMessage)
    assert "設定されていません" in reply.messages[0].text
    assert "WEATHER_LOCATIONS" in reply.messages[0].text


def test_execute_with_multiple_cities_newline_separated(monkeypatch):
    """改行区切りの複数都市設定でも正常に動作する結合テスト"""
    monkeypatch.setenv("WEATHER_LOCATIONS", "札幌\n名古屋\n京都")

    mock_line_adapter = MockMessagingAdapter()
    mock_weather_adapter = MagicMock()
    mock_weather_adapter.get_weather_text.side_effect = lambda city: f"{city}: 快晴"

    usecase = SendWeatherUsecase(mock_line_adapter, mock_weather_adapter)
    event = FakeEvent()

    usecase.execute(event, "天気")

    assert mock_weather_adapter.get_weather_text.call_count == 3
    mock_weather_adapter.get_weather_text.assert_any_call("札幌")
    mock_weather_adapter.get_weather_text.assert_any_call("名古屋")
    mock_weather_adapter.get_weather_text.assert_any_call("京都")

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    assert "札幌: 快晴" in replies[0].messages[0].text
    assert "名古屋: 快晴" in replies[0].messages[0].text
    assert "京都: 快晴" in replies[0].messages[0].text


def test_execute_with_empty_weather_locations(monkeypatch):
    """WEATHER_LOCATIONSが空文字の場合のエラーメッセージ結合テスト"""
    monkeypatch.setenv("WEATHER_LOCATIONS", "")

    mock_line_adapter = MockMessagingAdapter()
    mock_weather_adapter = MagicMock()

    usecase = SendWeatherUsecase(mock_line_adapter, mock_weather_adapter)
    event = FakeEvent()

    usecase.execute(event, "天気")

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    assert "設定されていません" in replies[0].messages[0].text
