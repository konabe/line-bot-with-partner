from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

from .protocols import LineAdapterProtocol, OpenAIAdapterProtocol


class SendMealUsecase:
    def __init__(
        self,
        line_adapter: LineAdapterProtocol,
        openai_adapter: OpenAIAdapterProtocol,
    ):
        self._line_adapter = line_adapter
        self._openai_adapter = openai_adapter

    def execute(self, event) -> None:
        try:
            suggestion = self._openai_adapter.get_chatgpt_meal_suggestion()
        except Exception:
            suggestion = None

        if not suggestion:
            msg = "申し訳ないです。おすすめを取得できませんでした。" " 管理者に OPENAI_API_KEY の設定を確認てもらってください。"
            reply_message_request = ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[TextMessage(text=msg, quickReply=None, quoteToken=None)],
                notificationDisabled=False,
            )
        else:
            reply_message_request = ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[
                    TextMessage(text=suggestion, quickReply=None, quoteToken=None)
                ],
                notificationDisabled=False,
            )

        self._line_adapter.reply_message(reply_message_request)
