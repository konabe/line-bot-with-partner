from ..infrastructure.logger import Logger
from typing import Callable, Optional
from linebot.v3.messaging.models import ReplyMessageRequest
from ..domain.services.janken_game_master_service import JankenGameMasterService
from .usecases.start_janken_game_usecase import StartJankenGameUsecase
from .types import PostbackEventLike


class PostbackHandler:
    def __init__(
        self,
        logger: Logger,
        safe_reply_message: Callable[[ReplyMessageRequest], None],
        profile_getter: Callable[[str], Optional[str]],
        janken_service: Optional[JankenGameMasterService] = None,
    ):
        self.logger: Logger = logger
        self._safe_reply: Callable[[ReplyMessageRequest], None] = safe_reply_message
        self._profile_getter: Callable[[str], Optional[str]] = profile_getter
        # ドメインサービスは注入可能にしてテスト容易性を確保
        self._janken_service: JankenGameMasterService = (
            janken_service or JankenGameMasterService()
        )

    def handle_postback(self, event: PostbackEventLike) -> None:
        """LINE からのポストバックイベントを処理します。"""
        data: str | None = event.postback.data
        self.logger.debug(f"handle_postback called. data: {data}")

        if data is None:
            self.logger.debug("handle_postback: postback.data is None, ignoring")
            return

        if data.startswith("janken:"):
            # 抽出した専用メソッドに委譲する
            self._handle_janken_postback(event)

    def _handle_janken_postback(self, event: PostbackEventLike) -> None:
        """'janken:' で始まるポストバックを処理する。ユースケースに委譲する。"""
        StartJankenGameUsecase(
            safe_reply_message=self._safe_reply,
            profile_getter=self._profile_getter,
            janken_service=self._janken_service,
        ).execute(event)
