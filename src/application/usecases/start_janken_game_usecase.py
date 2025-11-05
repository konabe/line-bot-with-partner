from typing import Optional

from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
from linebot.v3.webhooks.models.postback_event import PostbackEvent

from ...infrastructure.logger import Logger, create_logger
from .protocols import JankenServiceProtocol, LineAdapterProtocol


class StartJankenGameUsecase:
    def __init__(
        self,
        line_adapter: LineAdapterProtocol,
        janken_service: JankenServiceProtocol,
        logger: Optional[Logger] = None,
    ):
        self._line_adapter = line_adapter
        self._janken_service = janken_service
        self._logger = logger or create_logger(__name__)

    def execute(self, event: PostbackEvent) -> None:
        if not event.reply_token:
            self._logger.warning("reply_tokenが存在しないため、応答をスキップします")
            return

        if not event.postback or not event.postback.data:
            self._logger.warning("postback.dataが存在しないため、応答をスキップします")
            return

        try:
            user_hand_input = self._extract_user_hand(event.postback.data)
            user_label = self._get_user_label(event)
            reply_text = self._play_game(user_hand_input, user_label)
            self._send_reply(event.reply_token, reply_text)
        except Exception as e:
            self._logger.exception(f"じゃんけんゲーム実行中にエラーが発生: {e}")

    def _extract_user_hand(self, postback_data: str) -> str:
        return postback_data.split(":", 1)[1]

    def _get_user_label(self, event: PostbackEvent) -> str:
        if not event.source:
            return "あなた"

        user_id = getattr(event.source, "user_id", None)
        if not user_id:
            return "あなた"

        display_name = self._get_display_name(user_id)
        return f"あなた ({display_name})" if display_name else "あなた"

    def _get_display_name(self, user_id: str) -> Optional[str]:
        try:
            display_name = self._line_adapter.get_display_name_from_line_profile(
                user_id
            )
            if not display_name:
                self._logger.debug(
                    f"profile_getter returned no display name for user_id={user_id}"
                )
            return display_name
        except Exception as e:
            self._logger.error(f"ユーザー表示名の取得に失敗: {e}")
            return None

    def _play_game(self, user_hand_input: str, user_label: str) -> str:
        try:
            return self._janken_service.play_and_make_reply(user_hand_input, user_label)
        except ValueError as e:
            return f"{user_label}: {user_hand_input}\nエラー: {e}"

    def _send_reply(self, reply_token: str, text: str) -> None:
        reply_message_request = ReplyMessageRequest(
            replyToken=reply_token,
            messages=[TextMessage(text=text, quickReply=None, quoteToken=None)],
            notificationDisabled=False,
        )
        self._line_adapter.reply_message(reply_message_request)
