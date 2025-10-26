from typing import Callable
from linebot.v3.messaging.models import (
    TemplateMessage,
    ButtonsTemplate,
    PostbackAction,
    ReplyMessageRequest,
)


class SendJankenOptionsUsecase:
    def __init__(self, safe_reply_message: Callable[[ReplyMessageRequest], None]):
        self._safe_reply = safe_reply_message

    def execute(self, event) -> None:
        """イベント情報を受け取り、じゃんけんの選択テンプレートを返信する。"""
        template = TemplateMessage(
            alt_text="じゃんけんしましょう！",
            template=ButtonsTemplate(
                title="じゃんけん",
                text="どれを出しますか？",
                actions=[
                    PostbackAction(label="✊ グー", data="janken:✊"),
                    PostbackAction(label="✌️ チョキ", data="janken:✌️"),
                    PostbackAction(label="✋ パー", data="janken:✋"),
                ],
            ),
        )
        reply_message_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[template],
        )
        self._safe_reply(reply_message_request)
