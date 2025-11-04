from typing import Any, Optional

from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

from ...infrastructure.logger import Logger, create_logger
from .protocols import LineAdapterProtocol, OpenAIAdapterProtocol


class SendChatResponseUsecase:
    def __init__(
        self,
        line_adapter: LineAdapterProtocol,
        openai_adapter: OpenAIAdapterProtocol,
        logger: Optional[Logger] = None,
    ):
        self._line_adapter = line_adapter
        self._openai_adapter = openai_adapter
        self._logger = logger or create_logger(__name__)

    def execute(self, event: Any, user_message: str) -> None:
        """ChatGPTからの応答を取得してLINEに返信する

        Args:
            event: LINEイベント
            user_message: ユーザーからのメッセージ
        """
        try:
            response_text = self._get_response(user_message)
            self._send_reply(event.reply_token, response_text)
        except Exception as e:
            self._logger.exception(f"チャット応答の送信中にエラーが発生: {e}")

    def _get_response(self, user_message: str) -> str:
        """ChatGPTから応答を取得する

        Args:
            user_message: ユーザーからのメッセージ

        Returns:
            ChatGPTからの応答テキスト、または取得失敗時のエラーメッセージ
        """
        try:
            response = self._openai_adapter.get_chatgpt_response(user_message)
            if response:
                return response
        except Exception as e:
            self._logger.error(f"ChatGPT応答の取得に失敗: {e}")

        return "申し訳ないです。応答を生成できませんでした。管理者に OPENAI_API_KEY の設定を確認してもらってください。"

    def _send_reply(self, reply_token: str, text: str) -> None:
        """LINEに返信メッセージを送信する

        Args:
            reply_token: LINEの返信トークン
            text: 送信するテキスト
        """
        reply_message_request = ReplyMessageRequest(
            replyToken=reply_token,
            messages=[TextMessage(text=text, quickReply=None, quoteToken=None)],
            notificationDisabled=False,
        )
        self._line_adapter.reply_message(reply_message_request)
