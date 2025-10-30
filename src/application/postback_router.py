from typing import Optional

from ..domain.services.janken_game_master_service import JankenGameMasterService
from ..infrastructure.logger import Logger, create_logger
from .types import PostbackEventLike
from .usecases.start_janken_game_usecase import StartJankenGameUsecase


class PostbackRouter:
    def __init__(
        self,
        line_adapter,
        logger: Optional[Logger] = None,
        janken_service: Optional[JankenGameMasterService] = None,
    ):
        self.line_adapter = line_adapter
        self.logger = logger or create_logger(__name__)
        self.janken_service = janken_service or JankenGameMasterService()

    def route_postback(self, event: PostbackEventLike) -> None:
        data: str | None = event.postback.data
        self.logger.debug(f"route_postback called. data: {data}")

        if data is None:
            self.logger.debug("route_postback: postback.data is None, ignoring")
            return

        if data.startswith("janken:"):
            self._route_janken_postback(event)

    def _route_janken_postback(self, event: PostbackEventLike) -> None:
        StartJankenGameUsecase(
            line_adapter=self.line_adapter,
            janken_service=self.janken_service,
            logger=self.logger,
        ).execute(event)
