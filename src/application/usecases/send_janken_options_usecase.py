from linebot.v3.messaging.models import (
    ButtonsTemplate,
    PostbackAction,
    TemplateMessage,
)
from linebot.v3.webhooks.models.message_event import MessageEvent

from .base_usecase import BaseUsecase
from .protocols import LineAdapterProtocol


class SendJankenOptionsUsecase(BaseUsecase):
    def __init__(self, line_adapter: LineAdapterProtocol):
        super().__init__(line_adapter)

    def execute(self, event: MessageEvent) -> None:
        self._validate_reply_token(event)
        if not event.reply_token:
            return
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
        self._send_reply(event.reply_token, [template])
