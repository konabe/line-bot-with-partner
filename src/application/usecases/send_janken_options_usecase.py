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
            altText="じゃんけんしましょう！",
            template=ButtonsTemplate(
                title="じゃんけん",
                text="どれを出しますか？",
                actions=[
                    PostbackAction(
                        label="✊ グー",
                        data="janken:✊",
                        displayText=None,
                        inputOption=None,
                        fillInText=None,
                    ),
                    PostbackAction(
                        label="✌️ チョキ",
                        data="janken:✌️",
                        displayText=None,
                        inputOption=None,
                        fillInText=None,
                    ),
                    PostbackAction(
                        label="✋ パー",
                        data="janken:✋",
                        displayText=None,
                        inputOption=None,
                        fillInText=None,
                    ),
                ],
                thumbnailImageUrl=None,
                imageAspectRatio=None,
                imageSize=None,
                imageBackgroundColor=None,
                defaultAction=None,
            ),
            quickReply=None,
        )
        reply_message_request = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[template],
            notificationDisabled=False,
        )
        self._safe_reply(reply_message_request)
