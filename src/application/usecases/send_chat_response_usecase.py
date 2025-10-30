from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

from .protocols import LineAdapterProtocol, OpenAIAdapterProtocol


class SendChatResponseUsecase:
    def __init__(
        self,
        line_adapter: LineAdapterProtocol,
        openai_adapter: OpenAIAdapterProtocol,
    ):
        self._line_adapter = line_adapter
        self._openai_adapter = openai_adapter

    def execute(self, event, user_message: str) -> None:
        try:
            response = None
            try:
                response = self._openai_adapter.get_chatgpt_response(user_message)
            except Exception:
                response = None

            if not response:
                msg = "申し訳ないです。応答を生成できませんでした。" " 管理者に OPENAI_API_KEY の設定を確認してもらってください。"
                reply_message_request = ReplyMessageRequest(
                    replyToken=event.reply_token,
                    messages=[TextMessage(text=msg, quickReply=None, quoteToken=None)],
                    notificationDisabled=False,
                )
            else:
                reply_message_request = ReplyMessageRequest(
                    replyToken=event.reply_token,
                    messages=[
                        TextMessage(text=response, quickReply=None, quoteToken=None)
                    ],
                    notificationDisabled=False,
                )

            self._line_adapter.reply_message(reply_message_request)
        except Exception:
            return
