from linebot.v3.webhooks.models.message_event import MessageEvent

from ...domain.models.digimon_info import DigimonInfo
from ...infrastructure.line_model.digimon_button_template import (
    create_digimon_zukan_button_template,
)
from .base_usecase import BaseUsecase
from .protocols import DigimonAdapterProtocol, LineAdapterProtocol


class SendDigimonUsecase(BaseUsecase):
    def __init__(
        self,
        line_adapter: LineAdapterProtocol,
        digimon_adapter: DigimonAdapterProtocol,
    ):
        super().__init__(line_adapter)
        self.digimon_adapter = digimon_adapter

    def execute(self, event: MessageEvent) -> None:
        self._logger.info("デジモンリクエスト受信。図鑑風情報を返信")

        if not self._validate_reply_token(event):
            return

        info = self.digimon_adapter.get_random_digimon_info()
        if not info:
            if event.reply_token:
                self._send_error_reply(
                    event.reply_token, "デジモン図鑑情報の取得に失敗しました。"
                )
            return

        self._send_digimon_zukan_message(event, info)

    def _send_digimon_zukan_message(
        self, event: MessageEvent, info: DigimonInfo
    ) -> None:
        reply_token = event.reply_token
        if not reply_token:
            return

        try:
            candidate = create_digimon_zukan_button_template(info)
            self._send_reply(reply_token, [candidate])
        except Exception as e:
            self._logger.error(f"デジモンメッセージ送信エラー: {e}")
            self._send_error_reply(
                reply_token, "デジモン図鑑情報の取得に失敗しました。"
            )
