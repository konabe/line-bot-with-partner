from ..infrastructure.logger import Logger, create_logger
from typing import Callable, Optional
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
from ..domain.janken import JankenGame
from .types import PostbackEventLike


class PostbackHandler:
    def __init__(
        self,
        logger: Logger,
        safe_reply_message: Callable[[ReplyMessageRequest], None],
        profile_getter: Optional[Callable[[str], Optional[str]]] = None,
    ):
        self.logger: Logger = logger
        self._safe_reply: Callable[[ReplyMessageRequest], None] = safe_reply_message
        # profile_getter: function(user_id) -> display_name | None
        self._profile_getter: Optional[Callable[[str], Optional[str]]] = profile_getter

    def handle_postback(self, event: PostbackEventLike) -> None:
        """LINE からのポストバックイベントを処理します。"""
        data: str | None = event.postback.data
        self.logger.debug(f"handle_postback called. data: {data}")
        if data and data.startswith("janken:"):
            user_hand: str = data.split(":")[1]

            # attempt to resolve user id from event.source
            user_id = getattr(event.source, 'user_id', None) or getattr(event.source, 'userId', None)
            display_name: Optional[str] = None
            if user_id and self._profile_getter is not None:
                try:
                    display_name = self._profile_getter(user_id)
                except Exception as e:
                    self.logger.debug(f"profile_getter failed for {user_id}: {e}")

            user_label = f"あなた ({display_name})" if display_name else "あなた"

            game: JankenGame = JankenGame()
            try:
                result: dict[str, str] = game.play(user_hand)
                reply: str = (
                    f"{user_label}: {result['user_hand']}\n"
                    f"Bot: {result['bot_hand']}\n"
                    f"結果: {result['result']}"
                )
                self.logger.info(f"じゃんけん結果: {reply}")
            except ValueError as e:
                reply = f"{user_label}: {user_hand}\nエラー: {e}"
                self.logger.error(f"じゃんけんエラー: {e}")

            reply_message_request: ReplyMessageRequest = ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)]
            )
            self._safe_reply(reply_message_request)
