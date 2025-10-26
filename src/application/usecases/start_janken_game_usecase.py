from typing import Callable, Optional

from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

from ..types import PostbackEventLike
from ...domain.services.janken_game_master_service import JankenGameMasterService
from ...infrastructure.logger import create_logger, Logger




class StartJankenGameUsecase:
    """じゃんけん開始（ポストバック受信時）のユースケース

    コンストラクタで必要な外部依存（返信関数、プロファイル取得関数、ドメインサービス）を注入する。
    """

    def __init__(
        self,
        safe_reply_message: Callable[[ReplyMessageRequest], None],
        profile_getter: Callable[[str], Optional[str]],
        janken_service: Optional[JankenGameMasterService] = None,
        logger: Optional[Logger] = None,
    ):
        self._safe_reply = safe_reply_message
        self._profile_getter = profile_getter
        self._janken_service = janken_service or JankenGameMasterService()
        self._logger: Logger = logger or create_logger(__name__)

    def execute(self, event: PostbackEventLike) -> None:
        """event を受け取り、じゃんけんのプレイを実行して返信を送信する。"""
        data: str | None = event.postback.data
        if data is None:
            return

        user_hand_input: str = data.split(":", 1)[1]

        user_id = getattr(event.source, 'userId', None)
        display_name: Optional[str] = None
        if user_id:
            try:
                display_name = self._profile_getter(user_id)
            except Exception:
                # プロファイル取得失敗は無視してラベルはデフォルトにする
                display_name = None

        # ログにプロフィール取得の結果を残す（None の場合は取得できなかった旨）
        if user_id and not display_name:
            self._logger.debug(f"profile_getter returned no display name for user_id={user_id}")

        user_label = f"あなた ({display_name})" if display_name else "あなた"

        try:
            reply: str = self._janken_service.play_and_make_reply(user_hand_input, user_label)
        except ValueError as e:
            reply = f"{user_label}: {user_hand_input}\nエラー: {e}"

        reply_message_request: ReplyMessageRequest = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=reply)]
        )
        self._safe_reply(reply_message_request)
