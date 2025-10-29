from linebot.v3.messaging.models import (
    ButtonsTemplate,
    PostbackAction,
    ReplyMessageRequest,
    TemplateMessage,
)

from .protocols import LineAdapterProtocol


class SendJankenOptionsUsecase:
    def __init__(self, line_adapter: LineAdapterProtocol):
        self._line_adapter = line_adapter

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
        self._line_adapter.reply_message(reply_message_request)
