from typing import Any

from ...infrastructure.logger import create_logger
from .protocols import DigimonAdapterProtocol, LineAdapterProtocol

logger = create_logger(__name__)


class SendDigimonUsecase:
    def __init__(
        self, line_adapter: LineAdapterProtocol, digimon_adapter: DigimonAdapterProtocol
    ):
        self.line_adapter = line_adapter
        self.digimon_adapter = digimon_adapter

    def execute(self, event: Any) -> None:
        logger.info("デジモンリクエスト受信。デジモン情報を返信")

        info = self.digimon_adapter.get_random_digimon_info()
        if not info:
            self._send_error_message(event)
            return

        self._send_digimon_message(event, info)

    def _send_digimon_message(self, event: Any, info: Any) -> None:
        try:
            message_text = self._format_digimon_message(info)
            self._send_text_message(event, message_text)

        except Exception as e:
            logger.error(f"デジモンメッセージ送信エラー: {e}")
            self._send_error_message(event)

    def _format_digimon_message(self, info: Any) -> str:
        message_lines = [
            f"デジモン図鑑 No.{info.id}",
            f"名前: {info.name}",
            f"レベル: {info.level}",
        ]
        if info.image_url:
            message_lines.append(f"画像: {info.image_url}")

        return "\n".join(message_lines)

    def _send_text_message(self, event: Any, text: str) -> None:
        from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

        reply_message_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=text)],
            notificationDisabled=False,
        )
        self.line_adapter.reply_message(reply_message_request)

    def _send_error_message(self, event: Any) -> None:
        from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

        reply_message_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text="デジモン情報の取得に失敗しました")],
            notificationDisabled=False,
        )
        self.line_adapter.reply_message(reply_message_request)
