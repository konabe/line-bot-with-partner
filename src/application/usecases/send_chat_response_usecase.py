from typing import Optional

from linebot.v3.webhooks.models.message_event import MessageEvent

from ...infrastructure.logger import Logger
from .base_usecase import BaseUsecase
from .protocols import LineAdapterProtocol, OpenAIAdapterProtocol


class SendChatResponseUsecase(BaseUsecase):
    def __init__(
        self,
        line_adapter: LineAdapterProtocol,
        openai_adapter: OpenAIAdapterProtocol,
        logger: Optional[Logger] = None,
    ):
        super().__init__(line_adapter, logger)
        self._openai_adapter = openai_adapter

    def execute(self, event: MessageEvent, user_message: str) -> None:
        if not self._validate_reply_token(event):
            return

        try:
            response_text = self._get_response(user_message)
            if event.reply_token:
                self._send_text_reply(event.reply_token, response_text)
        except Exception as e:
            self._logger.exception(f"チャット応答の送信中にエラーが発生: {e}")

    def _get_response(self, user_message: str) -> str:
        try:
            response = self._openai_adapter.get_chatgpt_response(user_message)
            if response:
                return response
        except Exception as e:
            self._logger.error(f"ChatGPT応答の取得に失敗: {e}")

        return "申し訳ないです。応答を生成できませんでした。管理者に OPENAI_API_KEY の設定を確認してもらってください。"
