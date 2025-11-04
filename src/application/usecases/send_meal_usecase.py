from typing import Optional

from linebot.v3.messaging.models import (
    ButtonsTemplate,
    PostbackAction,
    ReplyMessageRequest,
    TemplateMessage,
    TextMessage,
)
from linebot.v3.webhooks.models.message_event import MessageEvent

from ...infrastructure.logger import Logger, create_logger
from .protocols import LineAdapterProtocol, OpenAIAdapterProtocol


class SendMealUsecase:
    def __init__(
        self,
        line_adapter: LineAdapterProtocol,
        openai_adapter: OpenAIAdapterProtocol,
        logger: Optional[Logger] = None,
    ):
        self._line_adapter = line_adapter
        self._openai_adapter = openai_adapter
        self._logger = logger or create_logger(__name__)

    def execute(self, event: MessageEvent) -> None:
        if not event.reply_token:
            self._logger.warning("reply_tokenが存在しないため、応答をスキップします")
            return

        try:
            suggestion, pl_request_id = self._get_meal_suggestion()
            messages = self._create_messages(suggestion, pl_request_id)
            self._send_reply(event.reply_token, messages)
        except Exception as e:
            self._logger.exception(f"料理提案の送信中にエラーが発生: {e}")

    def _get_meal_suggestion(self) -> tuple[Optional[str], Optional[int]]:
        try:
            result = self._openai_adapter.get_chatgpt_meal_suggestion(
                return_request_id=True
            )
            if isinstance(result, tuple):
                return result
            return result, None
        except Exception as e:
            self._logger.error(f"料理提案の取得に失敗: {e}")
            return None, None

    def _create_messages(
        self, suggestion: Optional[str], pl_request_id: Optional[int]
    ) -> list[TextMessage | TemplateMessage]:
        if not suggestion:
            error_msg = (
                "申し訳ないです。おすすめを取得できませんでした。"
                "管理者に OPENAI_API_KEY の設定を確認してもらってください。"
            )
            return [TextMessage(text=error_msg, quickReply=None, quoteToken=None)]

        messages: list[TextMessage | TemplateMessage] = [
            TextMessage(text=suggestion, quickReply=None, quoteToken=None)
        ]

        if pl_request_id is not None:
            feedback_template = self._create_feedback_template(pl_request_id)
            messages.append(feedback_template)

        return messages

    def _create_feedback_template(self, pl_request_id: int) -> TemplateMessage:
        return TemplateMessage(
            altText="料理提案の評価をお願いします",
            template=ButtonsTemplate(
                title="評価",
                text="この提案はいかがでしたか？",
                actions=[
                    PostbackAction(
                        label="😊 良い",
                        data=f"meal_feedback:{pl_request_id}:100",
                        displayText=None,
                        inputOption=None,
                        fillInText=None,
                    ),
                    PostbackAction(
                        label="😐 普通",
                        data=f"meal_feedback:{pl_request_id}:50",
                        displayText=None,
                        inputOption=None,
                        fillInText=None,
                    ),
                    PostbackAction(
                        label="😞 悪い",
                        data=f"meal_feedback:{pl_request_id}:0",
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

    def _send_reply(
        self, reply_token: str, messages: list[TextMessage | TemplateMessage]
    ) -> None:
        reply_message_request = ReplyMessageRequest(
            replyToken=reply_token,
            messages=messages,
            notificationDisabled=False,
        )
        self._line_adapter.reply_message(reply_message_request)
