"""ポケモン図鑑情報を送信するユースケース"""

from typing import Any

from ...infrastructure.line_model.zukan_button_template import (
    create_pokemon_zukan_button_template,
)
from ...infrastructure.logger import create_logger
from .protocols import LineAdapterProtocol

logger = create_logger(__name__)


class SendPokemonZukanUsecase:
    """ポケモン図鑑情報送信ユースケース"""

    def __init__(self, line_adapter: LineAdapterProtocol, pokemon_adapter: Any):
        self.line_adapter = line_adapter
        self.pokemon_adapter = pokemon_adapter

    def execute(self, event: Any) -> None:
        """ポケモン図鑑情報を取得して送信する"""
        logger.info("ポケモンリクエスト受信。図鑑風情報を返信")

        # ポケモン情報を取得
        info = self.pokemon_adapter.get_random_pokemon_info()
        if not info:
            self._send_error_message(event)
            return

        self._send_pokemon_zukan_message(event, info)

    def _send_pokemon_zukan_message(self, event: Any, info: Any) -> None:
        """ポケモン図鑑メッセージを送信"""
        try:
            candidate = create_pokemon_zukan_button_template(info)

            # LINE SDK v3対応のメッセージ送信
            self._send_line_message(event, candidate)

        except Exception as e:
            logger.error(f"ポケモンメッセージ送信エラー: {e}")
            self._send_error_message(event)

    def _send_line_message(self, event: Any, candidate: Any) -> None:
        """LINE SDKを使ってメッセージを送信"""
        try:
            # SDK v3形式での送信を試行
            if hasattr(candidate, "dict") and candidate.__class__.__name__ in (
                "TextMessage",
                "TemplateMessage",
            ):
                from linebot.v3.messaging.models import ReplyMessageRequest

                reply_message_request = ReplyMessageRequest(
                    replyToken=event.reply_token,
                    messages=[candidate],
                    notificationDisabled=False,
                )
                self.line_adapter.reply_message(reply_message_request)
                return

            # レガシー形式での送信をフォールバック
            from linebot.v3.messaging import models

            sdk_req = models.ReplyMessageRequest.parse_obj(
                {"replyToken": event.reply_token, "messages": [candidate]}
            )
            self.line_adapter.reply_message(sdk_req)

        except Exception as e:
            logger.error(f"LINE メッセージ送信エラー: {e}")
            raise

    def _send_error_message(self, event: Any) -> None:
        """エラーメッセージを送信"""
        from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

        reply_message_request = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[
                TextMessage(
                    text="ポケモン図鑑情報の取得に失敗しました。",
                    quickReply=None,
                    quoteToken=None,
                )
            ],
            notificationDisabled=False,
        )
        self.line_adapter.reply_message(reply_message_request)
