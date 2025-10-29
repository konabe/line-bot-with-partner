from typing import Any, Callable, Dict, Optional

from src.domain.services.janken_game_master_service import JankenGameMasterService


class FakeJankenGame:
    def __init__(self, behavior: Optional[Callable[[str], Dict[str, str]]] = None):
        self.behavior = behavior

    def play(self, user_hand_input: str) -> Dict[str, str]:
        if callable(self.behavior):
            return self.behavior(user_hand_input)
        # default deterministic response
        return {
            "user_hand": user_hand_input,
            "bot_hand": "✌️",
            "result": "あなたの勝ち！",
        }


def test_play_and_make_reply_success():
    fake_game = FakeJankenGame()
    svc = JankenGameMasterService(game=fake_game)  # type: ignore

    reply = svc.play_and_make_reply("✊", "あなた (Bob)")

    assert "あなた (Bob): ✊" in reply
    assert "Bot: ✌️" in reply
    assert "結果: あなたの勝ち！" in reply


def test_play_and_make_reply_invalid_hand():
    def raise_invalid(uh: str) -> Dict[str, str]:
        raise ValueError(f"無効な手です: {uh}")

    fake_game = FakeJankenGame(behavior=raise_invalid)
    svc = JankenGameMasterService(game=fake_game)  # type: ignore

    reply = svc.play_and_make_reply("invalid", "あなた")

    assert "あなた: invalid" in reply
    assert "エラー: 無効な手です: invalid" in reply
