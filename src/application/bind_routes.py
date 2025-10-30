import logging
from typing import Any, Optional

from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks.models.message_event import MessageEvent
from linebot.v3.webhooks.models.postback_event import PostbackEvent

from src.application.routes.message_router import MessageRouter
from src.application.routes.postback_router import PostbackRouter

from ..domain import OpenAIAdapter
from ..infrastructure.adapters.line_adapter import LineMessagingAdapter
from ..infrastructure.adapters.pokemon_adapter import PokemonApiAdapter
from ..infrastructure.adapters.weather_adapter import WeatherAdapter
from ..infrastructure.logger import Logger, create_logger
from .register_flask_routes import register_routes

logger = logging.getLogger(__name__)


def bind_routes(
    app: Any,
    handler: WebhookHandler,
    line_adapter: Optional[Any] = None,
    logger: Optional[Logger] = None,
) -> None:
    """Webhook ハンドラを登録する。

    - LineMessagingAdapter はテストで差し替え可能なように遅延生成する。
    - OpenAI クライアントは遅延初期化される（コストの高い初期化を回避）。
    """

    adapter_logger = logger or create_logger(__name__)
    _line_adapter = line_adapter or LineMessagingAdapter(logger=adapter_logger)

    register_routes(app, handler, _line_adapter)

    _openai_holder: dict = {"client": None}
    _weather_adapter = WeatherAdapter()
    _pokemon_adapter = PokemonApiAdapter()

    def _get_openai_client():
        if _openai_holder["client"] is None:
            _openai_holder["client"] = OpenAIAdapter()
        return _openai_holder["client"]

    # Router インスタンスを生成。Logger として adapter_logger を再利用する。
    message_router_instance = MessageRouter(
        _line_adapter,
        _get_openai_client(),
        _weather_adapter,
        _pokemon_adapter,
        logger=adapter_logger,
    )

    postback_router_instance = PostbackRouter(
        _line_adapter,
        logger=adapter_logger,
        janken_service=message_router_instance.janken_service,
    )

    handler.add(MessageEvent)(message_router_instance.route_message)
    handler.add(PostbackEvent)(postback_router_instance.route_postback)
