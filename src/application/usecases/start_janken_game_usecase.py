from typing import Optional

from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

from ...domain.services.janken_game_master_service import JankenGameMasterService
from ...infrastructure.logger import Logger, create_logger
from ..types import PostbackEventLike
from .protocols import LineAdapterProtocol


class StartJankenGameUsecase:
    """じゃんけん開始（ポストバック受信時）のユースケース

    コンストラクタで必要な外部依存（返信関数、プロファイル取得関数、ドメインサービス）を注入する。
    """

    def __init__(
        self,
        line_adapter: LineAdapterProtocol,
        janken_service: Optional[JankenGameMasterService] = None,
        logger: Optional[Logger] = None,
    ):
        self._line_adapter = line_adapter
        self._janken_service = janken_service or JankenGameMasterService()
        self._logger: Logger = logger or create_logger(__name__)

    def execute(self, event: PostbackEventLike) -> None:
        """event を受け取り、じゃんけんのプレイを実行して返信を送信する。"""
        data: str | None = event.postback.data
        if data is None:
            return

        user_hand_input: str = data.split(":", 1)[1]

        user_id = event.source.user_id
        display_name: Optional[str] = None
        if user_id:
            try:
                # Line adapter にプロフィール取得を委譲する
                display_name = self._line_adapter.get_display_name_from_line_profile(
                    user_id
                )
            except Exception:
                # プロファイル取得失敗は無視してラベルはデフォルトにする
                display_name = None

        # ログにプロフィール取得の結果を残す（None の場合は取得できなかった旨）
        if user_id and not display_name:
            self._logger.debug(
                f"profile_getter returned no display name for user_id={user_id}"
            )

        user_label = f"あなた ({display_name})" if display_name else "あなた"

        try:
            reply: str = self._janken_service.play_and_make_reply(
                user_hand_input, user_label
            )
        except ValueError as e:
            reply = f"{user_label}: {user_hand_input}\nエラー: {e}"

        reply_message_request: ReplyMessageRequest = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text=reply, quickReply=None, quoteToken=None)],
            notificationDisabled=False,
        )
        self._line_adapter.reply_message(reply_message_request)
