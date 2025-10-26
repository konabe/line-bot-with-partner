from typing import Callable
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage


class SendWeatherUsecase:
    """天気クエリのユースケース。

    役割:
    - テキストからロケーションを抽出する
    - 天気サービス（関数）を呼び出す
    - ReplyMessageRequest を作って返答する

    コンストラクタで依存を注入する（safe_reply_message, weather_getter）。
    """

    def __init__(self, safe_reply_message: Callable[[ReplyMessageRequest], None], weather_adapter):
        """Initialize with a safe reply function and a weather adapter instance.

        weather_adapter must provide a method `get_weather_text(location: str) -> str`.
        """
        self._safe_reply = safe_reply_message
        self._weather_adapter = weather_adapter

    def _extract_location_from_weather_query(self, text: str) -> str:
        import re
        match = re.search(r'(.+?)の天気', text)
        if match:
            return match.group(1).strip()
        return ""

    def execute(self, event, text: str) -> None:
        """event とユーザーテキストを受け取り、天気を問い合わせて返信する。"""
        loc = self._extract_location_from_weather_query(text)
        if loc:
            reply_text = self._weather_adapter.get_weather_text(loc)
        else:
            reply_text = self._weather_adapter.get_weather_text('東京')

        reply_message_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=reply_text)]
        )
        self._safe_reply(reply_message_request)
