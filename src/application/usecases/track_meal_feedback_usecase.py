from typing import Optional

from linebot.v3.webhooks.models.postback_event import PostbackEvent

from .base_usecase import BaseUsecase
from .protocols import LineAdapterProtocol, OpenAIAdapterProtocol


class TrackMealFeedbackUsecase(BaseUsecase):
    def __init__(
        self,
        line_adapter: LineAdapterProtocol,
        openai_adapter: OpenAIAdapterProtocol,
    ):
        super().__init__(line_adapter)
        self._openai_adapter = openai_adapter

    def execute(self, event: PostbackEvent, postback_data: str) -> bool:
        reply_token = event.reply_token
        if not reply_token:
            self._logger.warning("reply_tokenが存在しないため、応答をスキップします")
            return False

        parsed = self._parse_postback_data(postback_data)
        if parsed is None:
            return False

        pl_request_id, score = parsed

        try:
            success = self._track_score(pl_request_id, score)
            self._send_text_reply(reply_token, "評価ありがとうございます!😊")
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
