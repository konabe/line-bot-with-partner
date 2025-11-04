from typing import Optional

from ...infrastructure.logger import Logger, create_logger
from ..types import PostbackEventLike
from ..usecases.protocols import (
    JankenServiceProtocol,
    LineAdapterProtocol,
    OpenAIAdapterProtocol,
)
from ..usecases.start_janken_game_usecase import StartJankenGameUsecase
from ..usecases.track_meal_feedback_usecase import TrackMealFeedbackUsecase


class PostbackRouter:
    def __init__(
        self,
        line_adapter: LineAdapterProtocol,
        openai_adapter: OpenAIAdapterProtocol,
        janken_service: JankenServiceProtocol,
        logger: Optional[Logger] = None,
    ):
        self.line_adapter = line_adapter
        self.openai_adapter = openai_adapter
        self.logger = logger or create_logger(__name__)
        self.janken_service = janken_service

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
        usecase = TrackMealFeedbackUsecase(
            line_adapter=self.line_adapter,
            openai_adapter=self.openai_adapter,
            logger=self.logger,
        )
        usecase.execute(event, data)

    def _route_janken_postback(self, event: PostbackEventLike) -> None:
        StartJankenGameUsecase(
            line_adapter=self.line_adapter,
            janken_service=self.janken_service,
            logger=self.logger,
        ).execute(event)
