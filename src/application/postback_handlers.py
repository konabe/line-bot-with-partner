from typing import Optional

from ..domain.services.janken_game_master_service import JankenGameMasterService
from ..infrastructure.logger import Logger
from .types import PostbackEventLike
from .usecases.protocols import LineAdapterProtocol
from .usecases.start_janken_game_usecase import StartJankenGameUsecase


class PostbackHandler:
    def __init__(
        self,
        logger: Logger,
        line_adapter: LineAdapterProtocol,
        janken_service: Optional[JankenGameMasterService] = None,
    ):
        self.logger: Logger = logger
        self._line_adapter: LineAdapterProtocol = line_adapter
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
            line_adapter=self._line_adapter,
            janken_service=self._janken_service,
        ).execute(event)
