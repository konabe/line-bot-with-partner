from typing import Optional, Union

from linebot.v3.messaging.models import Message, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks.models.message_event import MessageEvent
from linebot.v3.webhooks.models.postback_event import PostbackEvent

from ...infrastructure.logger import Logger, create_logger
from .protocols import LineAdapterProtocol


class BaseUsecase:
    def __init__(
        self, line_adapter: LineAdapterProtocol, logger: Optional[Logger] = None
    ):
        self._line_adapter = line_adapter
        self._logger = logger or create_logger(self.__class__.__name__)

    def _validate_reply_token(
        self, event: Union[MessageEvent, PostbackEvent]
    ) -> bool:
        if not event.reply_token:
            self._logger.warning("reply_tokenが存在しないため、応答をスキップします")
            return False
        return True

    def _send_text_reply(self, reply_token: str, text: str) -> None:
        self._send_reply(
            reply_token, [TextMessage(text=text, quickReply=None, quoteToken=None)]
        )

    def _send_reply(self, reply_token: str, messages: list[Message]) -> None:
        reply_message_request = ReplyMessageRequest(
            replyToken=reply_token,
            messages=messages,
            notificationDisabled=False,
        )
        self._line_adapter.reply_message(reply_message_request)

    def _send_error_reply(self, reply_token: str, error_message: str) -> None:
        self._send_text_reply(reply_token, error_message)
