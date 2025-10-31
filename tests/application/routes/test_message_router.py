"""MessageRouter の単体テスト"""

from typing import Optional
from unittest.mock import MagicMock

import pytest

from src.application.routes.message_router import MessageRouter


class FakeLineAdapter:
    """テスト用 LINE アダプタ"""

    def __init__(self):
        self.reply_message_calls = []
        self.push_message_calls = []

    def reply_message(self, req):
        self.reply_message_calls.append(req)

    def push_message(self, req):
        self.push_message_calls.append(req)

    def get_display_name_from_line_profile(self, user_id: str) -> str:
        return "TestUser"


class FakeOpenAIAdapter:
    """テスト用 OpenAI アダプタ"""

    def __init__(self, response_text: str = "AI Response"):
        self.response_text = response_text
        self.get_chatgpt_response_calls = []
        self.get_chatgpt_meal_suggestion_calls = []

    def get_chatgpt_response(self, user_message: str) -> str:
        self.get_chatgpt_response_calls.append(user_message)
        return self.response_text

    def get_chatgpt_meal_suggestion(self, return_request_id=False):
        self.get_chatgpt_meal_suggestion_calls.append(True)
        if return_request_id:
            return self.response_text, 12345
        return self.response_text


class FakeWeatherAdapter:
    """テスト用天気アダプタ"""

    def __init__(self, weather_text: str = "晴れ"):
        self.weather_text = weather_text
        self.get_weather_text_calls = []

    def get_weather_text(self, location: str) -> str:
        self.get_weather_text_calls.append(location)
        return self.weather_text


class FakePokemonAdapter:
    """テスト用ポケモンアダプタ"""

    def __init__(self):
        self.get_random_pokemon_info_calls = []

    def get_random_pokemon_info(self):
        from src.domain.models.pokemon_info import PokemonInfo

        self.get_random_pokemon_info_calls.append(True)
        return PokemonInfo(
            zukan_no=25,
            name="ピカチュウ",
            types=["でんき"],
            image_url="https://example.com/pikachu.png",
        )


class FakeDigimonAdapter:
    """テスト用デジモンアダプタ"""

    def __init__(self):
        self.get_random_digimon_info_calls = []

    def get_random_digimon_info(self):
        from src.domain.models.digimon_info import DigimonInfo

        self.get_random_digimon_info_calls.append(True)
        return DigimonInfo(
            id=1,
            name="Agumon",
            level="Rookie",
            image_url="https://example.com/agumon.png",
        )


class FakeLogger:
    """テスト用ロガー"""

    def __init__(self):
        self.debug_logs = []
        self.error_logs = []
        self.info_logs = []
        self.warning_logs = []
        self.exception_logs = []

    def debug(self, msg, *args):
        self.debug_logs.append(msg)

    def error(self, msg, *args):
        self.error_logs.append(msg)

    def info(self, msg, *args):
        self.info_logs.append(msg)

    def warning(self, msg, *args):
        self.warning_logs.append(msg)

    def exception(self, msg, *args):
        self.exception_logs.append(msg)


def _make_message_event(text: str, user_id: str = "U123"):
    """MessageEvent 風のオブジェクトを作成"""

    class FakeMessage:
        def __init__(self, text: str):
            self.text = text
            self.type = "text"

    class FakeSource:
        def __init__(self, user_id: str):
            self.user_id = user_id
            self.type = "user"

    class FakeEvent:
        def __init__(self, text: str, user_id: str):
            self.message = FakeMessage(text)
            self.reply_token = "dummy_token"
            self.source = FakeSource(user_id)
            self.type = "message"

    return FakeEvent(text, user_id)


class TestMessageRouterEventHandling:
    """route_message の event 引数処理テスト"""

    def test_route_message_with_none_event_logs_error_and_returns(self):
        """event=None の場合、エラーログを出して早期リターンすること"""
        line_adapter = FakeLineAdapter()
        openai_adapter = FakeOpenAIAdapter()
        weather_adapter = FakeWeatherAdapter()

        router = MessageRouter(
            line_adapter,
            openai_adapter,
            weather_adapter,
            pokemon_adapter=None,
        )

        # event=None で呼び出し
        router.route_message(event=None)

        # アダプタが呼ばれていないことを確認（エラーログはモジュールレベルのロガーに出るため検証しない）
        assert len(line_adapter.reply_message_calls) == 0

    def test_route_message_with_extra_argument(self):
        """extra 引数が渡された場合もテキスト抽出できること"""
        line_adapter = FakeLineAdapter()
        openai_adapter = FakeOpenAIAdapter()
        weather_adapter = FakeWeatherAdapter("快晴です")
        logger = FakeLogger()

        router = MessageRouter(
            line_adapter,
            openai_adapter,
            weather_adapter,
            pokemon_adapter=None,
            logger=logger,
        )

        event = _make_message_event("東京の天気")

        # extra に文字列を渡す（本番で見られたパターン）
        router.route_message(event, extra="U123")

        # 天気ルートが呼ばれていることを確認
        assert len(weather_adapter.get_weather_text_calls) == 1


class TestMessageRouterWeatherRoute:
    """天気ルーティングのテスト"""

    def test_route_weather_message(self):
        """「天気」を含むメッセージが天気 usecase に委譲されること"""
        line_adapter = FakeLineAdapter()
        openai_adapter = FakeOpenAIAdapter()
        weather_adapter = FakeWeatherAdapter("晴れ")
        logger = FakeLogger()

        router = MessageRouter(
            line_adapter,
            openai_adapter,
            weather_adapter,
            pokemon_adapter=None,
            logger=logger,
        )

        event = _make_message_event("東京の天気")
        router.route_message(event)

        # weather_adapter が呼ばれていることを確認
        assert len(weather_adapter.get_weather_text_calls) == 1
        assert weather_adapter.get_weather_text_calls[0] == "東京"


class TestMessageRouterJankenRoute:
    """じゃんけんルーティングのテスト"""

    def test_route_janken_message(self):
        """「じゃんけん」メッセージがじゃんけん usecase に委譲されること"""
        line_adapter = FakeLineAdapter()
        openai_adapter = FakeOpenAIAdapter()
        weather_adapter = FakeWeatherAdapter()
        logger = FakeLogger()

        router = MessageRouter(
            line_adapter,
            openai_adapter,
            weather_adapter,
            pokemon_adapter=None,
            logger=logger,
        )

        event = _make_message_event("じゃんけん")
        router.route_message(event)

        # line_adapter.reply_message が呼ばれていることを確認
        assert len(line_adapter.reply_message_calls) == 1


class TestMessageRouterMealRoute:
    """今日のご飯ルーティングのテスト"""

    def test_route_meal_message(self):
        """「今日のご飯」メッセージがご飯 usecase に委譲されること"""
        line_adapter = FakeLineAdapter()
        openai_adapter = FakeOpenAIAdapter("カレーライス")
        weather_adapter = FakeWeatherAdapter()
        logger = FakeLogger()

        router = MessageRouter(
            line_adapter,
            openai_adapter,
            weather_adapter,
            pokemon_adapter=None,
            logger=logger,
        )

        event = _make_message_event("今日のご飯")
        router.route_message(event)

        # OpenAI が呼ばれていることを確認
        assert len(openai_adapter.get_chatgpt_meal_suggestion_calls) == 1


class TestMessageRouterPokemonRoute:
    """ポケモンルーティングのテスト"""

    def test_route_pokemon_message(self):
        """「ポケモン」メッセージがポケモン usecase に委譲されること"""
        line_adapter = FakeLineAdapter()
        openai_adapter = FakeOpenAIAdapter()
        weather_adapter = FakeWeatherAdapter()
        pokemon_adapter = FakePokemonAdapter()
        logger = FakeLogger()

        router = MessageRouter(
            line_adapter,
            openai_adapter,
            weather_adapter,
            pokemon_adapter=pokemon_adapter,
            logger=logger,
        )

        event = _make_message_event("ポケモン")
        router.route_message(event)

        # line_adapter.reply_message が呼ばれていることを確認（図鑑テンプレート送信）
        assert len(line_adapter.reply_message_calls) == 1


class TestMessageRouterDigimonRoute:
    """デジモンルーティングのテスト"""

    def test_route_digimon_message(self):
        """「デジモン」メッセージがデジモン usecase に委譲されること"""
        line_adapter = FakeLineAdapter()
        openai_adapter = FakeOpenAIAdapter()
        weather_adapter = FakeWeatherAdapter()
        digimon_adapter = FakeDigimonAdapter()
        logger = FakeLogger()

        router = MessageRouter(
            line_adapter,
            openai_adapter,
            weather_adapter,
            pokemon_adapter=None,
            digimon_adapter=digimon_adapter,
            logger=logger,
        )

        event = _make_message_event("デジモン")
        router.route_message(event)

        assert len(digimon_adapter.get_random_digimon_info_calls) == 1
        assert len(line_adapter.reply_message_calls) == 1


class TestMessageRouterChatGPTRoute:
    """ChatGPT ルーティングのテスト"""

    def test_route_chatgpt_message(self):
        """「ぐんまちゃん、」で始まるメッセージが ChatGPT usecase に委譲されること"""
        line_adapter = FakeLineAdapter()
        openai_adapter = FakeOpenAIAdapter("こんにちは！")
        weather_adapter = FakeWeatherAdapter()
        logger = FakeLogger()

        router = MessageRouter(
            line_adapter,
            openai_adapter,
            weather_adapter,
            pokemon_adapter=None,
            logger=logger,
        )

        event = _make_message_event("ぐんまちゃん、こんにちは")
        router.route_message(event)

        # OpenAI が呼ばれていることを確認
        assert len(openai_adapter.get_chatgpt_response_calls) == 1


class TestMessageRouterUnmatchedMessage:
    """どのルートにも該当しないメッセージのテスト"""

    def test_unmatched_message_does_not_call_adapters(self):
        """該当しないメッセージは何も呼ばれないこと"""
        line_adapter = FakeLineAdapter()
        openai_adapter = FakeOpenAIAdapter()
        weather_adapter = FakeWeatherAdapter()
        logger = FakeLogger()

        router = MessageRouter(
            line_adapter,
            openai_adapter,
            weather_adapter,
            pokemon_adapter=None,
            logger=logger,
        )

        event = _make_message_event("普通のメッセージ")
        router.route_message(event)

        # どのアダプタも呼ばれないことを確認
        assert len(line_adapter.reply_message_calls) == 0
        assert len(openai_adapter.get_chatgpt_response_calls) == 0
        assert len(openai_adapter.get_chatgpt_meal_suggestion_calls) == 0
        assert len(weather_adapter.get_weather_text_calls) == 0
