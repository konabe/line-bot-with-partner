from typing import Optional

from ..models.janken import JankenGame


class JankenGameMasterService:
    def __init__(self, game: Optional[JankenGame] = None):
        self._game: JankenGame = game or JankenGame()

    def play_and_make_reply(self, user_hand_input: str, user_label: str) -> str:
        try:
            result = self._game.play(user_hand_input)
            reply = (
                f"{user_label}: {result['user_hand']}\n"
                f"Bot: {result['bot_hand']}\n"
                f"結果: {result['result']}"
            )
        except ValueError as e:
            reply = f"{user_label}: {user_hand_input}\nエラー: {e}"

        return reply
