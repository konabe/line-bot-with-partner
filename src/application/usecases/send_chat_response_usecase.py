from typing import Callable

from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage


class SendChatResponseUsecase:
    """汎用的な ChatGPT 応答ユースケース。

    コンストラクタで safe_reply_message と chatgpt_callable を注入する。
    chatgpt_callable は (user_message: str) -> str を返す callable を想定します。
    """

    def __init__(
        self,
        safe_reply_message: Callable[[ReplyMessageRequest], None],
        chatgpt_callable: Callable[[str], str],
    ):
        self._safe_reply = safe_reply_message
        self._chatgpt = chatgpt_callable

    def execute(self, event, user_message: str) -> None:
        """user_message に対してチャット応答を取得し、ReplyMessageRequest を送信する。"""
        try:
            response = self._chatgpt(user_message)
        except Exception:
            response = None

        if not response:
            msg = "申し訳ないです。応答を生成できませんでした。" "管理者に OPENAI_API_KEY の設定を確認してもらってください。"
            reply_message_request = ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[TextMessage(text=msg, quickReply=None, quoteToken=None)],
                notificationDisabled=False,
            )
        else:
            reply_message_request = ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[TextMessage(text=response, quickReply=None, quoteToken=None)],
                notificationDisabled=False,
            )

        self._safe_reply(reply_message_request)
