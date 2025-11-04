from typing import Optional

from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

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

    def execute(self, event, postback_data: str) -> bool:
        """料理提案の評価をPromptLayerに送信する

        Args:
            event: LINEイベント
            postback_data: postbackのdata文字列 (形式: "meal_feedback:{pl_request_id}:{score}")

        Returns:
            スコア送信の成功/失敗
        """
        parsed = self._parse_postback_data(postback_data)
        if parsed is None:
            return False

        pl_request_id, score = parsed

        success = self._openai_adapter.track_score(
            request_id=pl_request_id, score=score, score_name="user_feedback"
        )

        feedback_msg = "評価ありがとうございます!😊"
        reply_message_request = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text=feedback_msg, quickReply=None, quoteToken=None)],
            notificationDisabled=False,
        )
        self._line_adapter.reply_message(reply_message_request)

        return success

    def _parse_postback_data(self, data: str) -> Optional[tuple[int, int]]:
        """postback dataをパースする

        Args:
            data: postbackのdata文字列 (形式: "meal_feedback:{pl_request_id}:{score}")

        Returns:
            (pl_request_id, score) のタプル、パース失敗時はNone
        """
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
