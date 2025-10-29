from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

from .protocols import LineAdapterProtocol, WeatherAdapterProtocol


class SendWeatherUsecase:
    """天気クエリのユースケース。

    コンストラクタで依存を注入する（LineAdapter, WeatherAdapter）。
    """

    def __init__(
        self, line_adapter: LineAdapterProtocol, weather_adapter: WeatherAdapterProtocol
    ):
        """Initialize with a Line adapter and a weather adapter instance.

        weather_adapter must provide a method `get_weather_text(location: str) -> str`.
        """
        self._line_adapter = line_adapter
        self._weather_adapter = weather_adapter

    def _extract_location_from_weather_query(self, text: str) -> str:
        import re

        match = re.search(r"(.+?)の天気", text)
        if match:
            return match.group(1).strip()
        return ""

    def execute(self, event, text: str) -> None:
        """event とユーザーテキストを受け取り、天気を問い合わせて返信する。"""
        t = text.strip()

        # ユーザーが正確に "天気" とだけ送った場合、環境変数から複数都市を読み一覧表示する
        if t == "天気":
            import os

            cfg = os.environ.get("WEATHER_LOCATIONS")
            if not cfg:
                reply_text = (
                    "表示する都市が設定されていません。環境変数 WEATHER_LOCATIONS にカンマ区切りの都市名を設定してください。"
                )
            else:
                # カンマまたは改行・空白で区切られている想定
                parts = [
                    p.strip() for p in cfg.replace("\n", ",").split(",") if p.strip()
                ]
                if not parts:
                    reply_text = (
                        "表示する都市が設定されていません。環境変数 WEATHER_LOCATIONS にカンマ区切りの都市名を設定してください。"
                    )
                else:
                    texts = []
                    for city in parts:
                        texts.append(self._weather_adapter.get_weather_text(city))
                    # 各都市の結果を2行改行で区切ってまとめる
                    reply_text = "\n\n".join(texts)
        else:
            loc = self._extract_location_from_weather_query(text)
            if loc:
                reply_text = self._weather_adapter.get_weather_text(loc)
            else:
                reply_text = self._weather_adapter.get_weather_text("東京")

        reply_message_request = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text=reply_text, quickReply=None, quoteToken=None)],
            notificationDisabled=False,
        )
        self._line_adapter.reply_message(reply_message_request)
