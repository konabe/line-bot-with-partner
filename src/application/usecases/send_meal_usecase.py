from typing import Callable

from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage


class SendMealUsecase:
    """今日のご飯リクエストを処理するユースケース。

    コンストラクタで依存を注入する（safe_reply_message, meal_suggester）。
    meal_suggester は引数無しで推薦テキストを返す callable を想定します。
    """

    def __init__(
        self,
        safe_reply_message: Callable[[ReplyMessageRequest], None],
        meal_suggester: Callable[[], str],
    ):
        self._safe_reply = safe_reply_message
        self._meal_suggester = meal_suggester

    def execute(self, event) -> None:
        """event を受け取り、ChatGPT からの推薦を取得して返信する。"""
        try:
            suggestion = self._meal_suggester()
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

        self._safe_reply(reply_message_request)
