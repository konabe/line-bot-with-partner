import logging
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks.models.message_event import MessageEvent
from linebot.v3.webhooks.models.text_message_content import TextMessageContent
from linebot.v3.webhooks.models.postback_event import PostbackEvent
from .message_handlers import MessageHandler
from .postback_handlers import PostbackHandler
from ..infrastructure.logger import create_logger
from .routes import register_routes

logger = logging.getLogger(__name__)

def register_handlers(app, handler: WebhookHandler, safe_reply_message):
    # ルートを登録
    register_routes(app, handler, safe_reply_message)

    # デフォルトの DomainServices をここで生成（遅延で OpenAIClient を生成）
    from src.domain import UMIGAME_STATE, is_closed_question
    from src.domain import OpenAIClient
    from src.infrastructure.weather_adapter import WeatherAdapter
    from types import SimpleNamespace

    _openai_holder = {"client": None}
    _weather_adapter = WeatherAdapter()

    def _get_openai_client():
        if _openai_holder["client"] is None:
            _openai_holder["client"] = OpenAIClient()
        return _openai_holder["client"]

    default_domain_services = SimpleNamespace(
        UMIGAME_STATE=UMIGAME_STATE,
        is_closed_question=is_closed_question,
        generate_umigame_puzzle=lambda: _get_openai_client().generate_umigame_puzzle(),
        call_openai_yesno_with_secret=lambda text, secret: _get_openai_client().call_openai_yesno_with_secret(text, secret),
        get_chatgpt_meal_suggestion=lambda: _get_openai_client().get_chatgpt_meal_suggestion(),
        get_chatgpt_response=lambda text: _get_openai_client().get_chatgpt_response(text),
        get_weather_text=lambda location: _weather_adapter.get_weather_text(location),
    )

    message_handler_instance = MessageHandler(safe_reply_message, default_domain_services)

    def message_handler(event):
        return message_handler_instance.handle_message(event)

    # Instantiate PostbackHandler with injected logger and safe_reply_message
    # profile_getter: lazily use requests to call LINE profile API if possible.
    def _profile_getter(user_id: str) -> str | None:
        import os
        try:
            import requests
        except Exception:
            logger.debug("requests not available; skipping profile fetch")
            return None

        token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
        if not token or not user_id:
            return None
        try:
            resp = requests.get(
                f"https://api.line.me/v2/bot/profile/{user_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=2,
            )
            if resp.status_code == 200:
                return resp.json().get('displayName')
        except Exception as e:
            logger.error(f"Failed to fetch profile for {user_id}: {e}")
        return None

    _postback_handler_instance = PostbackHandler(create_logger(__name__), safe_reply_message, _profile_getter)

    def postback_handler(event):
        return _postback_handler_instance.handle_postback(event)

    handler.add(MessageEvent, message=TextMessageContent)(message_handler)
    handler.add(PostbackEvent)(postback_handler)
