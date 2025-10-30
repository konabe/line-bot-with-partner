from typing import Any, Optional, cast

from ..domain.services.janken_game_master_service import JankenGameMasterService
from ..infrastructure.logger import Logger, create_logger
from .usecases.protocols import (
    LineAdapterProtocol,
    OpenAIAdapterProtocol,
    WeatherAdapterProtocol,
)
from .usecases.send_chat_response_usecase import SendChatResponseUsecase
from .usecases.send_janken_options_usecase import SendJankenOptionsUsecase
from .usecases.send_meal_usecase import SendMealUsecase
from .usecases.send_pokemon_zukan_usecase import SendPokemonZukanUsecase
from .usecases.send_weather_usecase import SendWeatherUsecase

logger = create_logger(__name__)


class MessageRouter:
    """LINEメッセージイベントとポストバックイベントをルーティングするクラス"""

    def __init__(
        self,
        line_adapter: LineAdapterProtocol,
        openai_adapter: OpenAIAdapterProtocol,
        weather_adapter: WeatherAdapterProtocol,
        pokemon_adapter=None,
        logger: Optional[Logger] = None,
        janken_service: Optional[JankenGameMasterService] = None,
    ):
        # adapter を直接注入する（DomainServices を廃止）
        self.line_adapter = line_adapter
        self.openai_adapter = openai_adapter
        self.weather_adapter = weather_adapter
        self.pokemon_adapter = pokemon_adapter
        self.logger = logger or create_logger(__name__)
        # ドメインサービスは注入可能にしてテスト容易性を確保
        self.janken_service = janken_service or JankenGameMasterService()

    def route_message(self, event) -> None:
        """LINE からのテキストメッセージイベントをルーティングします。"""
        text = event.message.text
        logger.debug(f"route_message called. text: {text}")

        t = text.strip()
        if "天気" in text:
            return self._route_weather(event, text)
        if t == "じゃんけん":
            return self._route_janken(event)
        if t == "今日のご飯":
            return self._route_meal(event)
        if t == "ポケモン":
            return self._route_pokemon_zukan(event)
        if t.startswith("ぐんまちゃん、"):
            return self._route_chatgpt(event, text)

    def _route_weather(self, event, text: str) -> None:
        logger.info("天気リクエスト検出: usecase に委譲")
        SendWeatherUsecase(self.line_adapter, self.weather_adapter).execute(event, text)

    def _route_janken(self, event) -> None:
        logger.info("じゃんけんテンプレートを送信 (usecase に委譲)")
        SendJankenOptionsUsecase(self.line_adapter).execute(event)

    def _route_meal(self, event) -> None:
        logger.info("今日のご飯リクエストを受信: usecase に委譲")
        SendMealUsecase(self.line_adapter, self.openai_adapter).execute(event)

    def _route_pokemon_zukan(self, event) -> None:
        logger.info("ポケモンリクエスト受信: usecase に委譲")
        SendPokemonZukanUsecase(self.line_adapter, self.pokemon_adapter).execute(event)

    def _route_chatgpt(self, event, text: str) -> None:
        logger.info("コマンド以外のメッセージを受信: usecase に委譲")
        SendChatResponseUsecase(
            cast(Any, self.line_adapter), cast(Any, self.openai_adapter)
        ).execute(event, text)
