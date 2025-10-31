from typing import Optional

from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

from ...domain.services.janken_game_master_service import JankenGameMasterService
from ...infrastructure.logger import Logger, create_logger
from ..types import PostbackEventLike
from ..usecases.start_janken_game_usecase import StartJankenGameUsecase


class PostbackRouter:
    def __init__(
        self,
        line_adapter,
        openai_adapter=None,
        logger: Optional[Logger] = None,
        janken_service: Optional[JankenGameMasterService] = None,
    ):
        self.line_adapter = line_adapter
        self.openai_adapter = openai_adapter
        self.logger = logger or create_logger(__name__)
        self.janken_service = janken_service or JankenGameMasterService()

    def route_postback(self, *args, **kwargs) -> None:
        # Be permissive about calling convention: webhook handler may call
        # with (event) or (event, parsed_postback). Try to infer the event.
        event = kwargs.get("event")
        if len(args) == 1:
            candidate = args[0]
            # Heuristic: event-like objects have reply_token or source attributes
            if (
                hasattr(candidate, "reply_token")
                or hasattr(candidate, "replyToken")
                or hasattr(candidate, "source")
            ):
                event = candidate
            else:
                # If it's not event-like, assume it's a parsed message/postback object
                # and try to find event in kwargs or elsewhere (not available here).
                event = kwargs.get("event")
        elif len(args) >= 2:
            event = args[0]

        if event is None:
            self.logger.error(
                "route_postback called but no event object could be inferred; skipping"
            )
            return

        data: str | None = getattr(getattr(event, "postback", None), "data", None)
        self.logger.debug(f"route_postback called. data: {data}")

        if data is None:
            self.logger.debug("route_postback: postback.data is None, ignoring")
            return

        if data.startswith("janken:"):
            self._route_janken_postback(event)
        elif data.startswith("meal_feedback:"):
            self._route_meal_feedback_postback(event, data)

    def _route_meal_feedback_postback(
        self, event: PostbackEventLike, data: str
    ) -> None:
        # data format: "meal_feedback:{pl_request_id}:{score}"
        parts = data.split(":")
        if len(parts) != 3:
            self.logger.warning(f"Invalid meal_feedback data format: {data}")
            return

        try:
            pl_request_id = int(parts[1])
            score = int(parts[2])
        except ValueError:
            self.logger.warning(f"Invalid meal_feedback data values: {data}")
            return

        if self.openai_adapter is None:
            self.logger.warning("openai_adapter not set, cannot track score")
            return

        # スコアをPromptLayerに送信
        success = self.openai_adapter.track_score(
            request_id=pl_request_id, score=score, score_name="user_feedback"
        )

        # ユーザーに感謝のメッセージを返信
        feedback_msg = "評価ありがとうございます！😊"
        reply_message_request = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text=feedback_msg, quickReply=None, quoteToken=None)],
            notificationDisabled=False,
        )
        self.line_adapter.reply_message(reply_message_request)

        if success:
            self.logger.info(f"Successfully tracked meal feedback: score={score}")
        else:
            self.logger.warning(f"Failed to track meal feedback: score={score}")

    def _route_janken_postback(self, event: PostbackEventLike) -> None:
        StartJankenGameUsecase(
            line_adapter=self.line_adapter,
            janken_service=self.janken_service,
            logger=self.logger,
        ).execute(event)
