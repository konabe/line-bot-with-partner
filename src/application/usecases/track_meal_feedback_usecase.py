from typing import Optional

from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
from linebot.v3.webhooks.models.postback_event import PostbackEvent

from ...infrastructure.logger import Logger, create_logger
from .protocols import LineAdapterProtocol, OpenAIAdapterProtocol


class TrackMealFeedbackUsecase:
    def __init__(
        self,
        line_adapter: LineAdapterProtocol,
        openai_adapter: OpenAIAdapterProtocol,
        logger: Optional[Logger] = None,
    ):
        self._line_adapter = line_adapter
        self._openai_adapter = openai_adapter
        self._logger = logger or create_logger(__name__)

    def execute(self, event: PostbackEvent, postback_data: str) -> bool:
        if not event.reply_token:
            self._logger.warning("reply_tokenが存在しないため、応答をスキップします")
            return False

        parsed = self._parse_postback_data(postback_data)
        if parsed is None:
            return False

        pl_request_id, score = parsed

        try:
            success = self._track_score(pl_request_id, score)
            self._send_feedback_message(event.reply_token)
            return success
        except Exception as e:
            self._logger.exception(f"フィードバック処理中にエラーが発生: {e}")
            return False

    def _parse_postback_data(self, data: str) -> Optional[tuple[int, int]]:
        parts = data.split(":")
        if len(parts) != 3:
            self._logger.warning(f"Invalid meal_feedback data format: {data}")
            return None

        try:
            pl_request_id = int(parts[1])
            score = int(parts[2])
            return (pl_request_id, score)
        except ValueError:
            self._logger.warning(f"Invalid meal_feedback data values: {data}")
            return None

    def _track_score(self, request_id: int, score: int) -> bool:
        return self._openai_adapter.track_score(
            request_id=request_id, score=score, score_name="user_feedback"
        )

    def _send_feedback_message(self, reply_token: str) -> None:
        feedback_msg = "評価ありがとうございます!😊"
        reply_message_request = ReplyMessageRequest(
            replyToken=reply_token,
            messages=[TextMessage(text=feedback_msg, quickReply=None, quoteToken=None)],
            notificationDisabled=False,
        )
        self._line_adapter.reply_message(reply_message_request)
