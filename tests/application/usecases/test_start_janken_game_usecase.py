from typing import Optional
from unittest.mock import Mock

from src.application.usecases.start_janken_game_usecase import StartJankenGameUsecase


class FakeLineAdapter:
    def __init__(self, fn, display_name_provider=None):
        self._fn = fn
        self._display_name_provider = display_name_provider

    def reply_message(self, req):
        return self._fn(req)

    def push_message(self, req):
        pass

    def get_display_name_from_line_profile(self, user_id: str) -> str:
        if self._display_name_provider is None:
            return "Alice"
        return self._display_name_provider(user_id)


def _make_event(data: Optional[str], user_id: str = "U111"):
    event = Mock()
    event.reply_token = "rtok"
    event.postback = Mock()
    event.postback.data = data
    event.source = Mock()
    event.source.user_id = user_id
    return event


def test_execute_success_with_profile():
    sent = []

    def fake_safe_reply(req):
        sent.append(req)

    class FakeJankenService:
        def play_and_make_reply(self, user_hand_input: str, user_label: str) -> str:
            return f"{user_label}: {user_hand_input}\nBot: ✌️\n結果: あなたの勝ち！"

    svc = StartJankenGameUsecase(
        FakeLineAdapter(fake_safe_reply, lambda uid: "Alice"), janken_service=FakeJankenService()  # type: ignore
    )
    event = _make_event("janken:✊")

    svc.execute(event)

    assert len(sent) == 1
    req = sent[0]
    text = req.messages[0].text
    assert "あなた (Alice): ✊" in text
    assert "Bot: ✌️" in text


def test_execute_profile_getter_raises_uses_default_label():
    sent = []

    def fake_safe_reply(req):
        sent.append(req)

    def bad_profile_getter(_):
        raise RuntimeError("profile failed")

    class FakeJankenService:
        def play_and_make_reply(self, user_hand_input: str, user_label: str) -> str:
            return f"{user_label}: {user_hand_input}\nBot: ✌️\n結果: あいこ"

    svc = StartJankenGameUsecase(
        FakeLineAdapter(fake_safe_reply, bad_profile_getter), janken_service=FakeJankenService()  # type: ignore
    )
    event = _make_event("janken:✋")

    svc.execute(event)

    assert len(sent) == 1
    req = sent[0]
    text = req.messages[0].text
    assert text.startswith("あなた: ✋")


def test_execute_janken_service_raises_value_error_returns_error_reply():
    sent = []

    def fake_safe_reply(req):
        sent.append(req)

    class BadService:
        def play_and_make_reply(self, user_hand_input: str, user_label: str) -> str:
            raise ValueError(f"無効な手です: {user_hand_input}")

    svc = StartJankenGameUsecase(
        FakeLineAdapter(fake_safe_reply, lambda uid: "Bob"),
        janken_service=BadService(),  # type: ignore
    )
    event = _make_event("janken:invalid")

    svc.execute(event)

    assert len(sent) == 1
    req = sent[0]
    text = req.messages[0].text
    assert "エラー: 無効な手です: invalid" in text


def test_execute_with_none_data_does_not_send():
    sent = []

    def fake_safe_reply(req):
        sent.append(req)

    class FakeJankenService:
        def play_and_make_reply(self, user_hand_input: str, user_label: str) -> str:
            return ""

    svc = StartJankenGameUsecase(
        FakeLineAdapter(fake_safe_reply, lambda uid: "Bob"),
        janken_service=FakeJankenService(),  # type: ignore
    )
    event = _make_event(None)

    svc.execute(event)

    assert sent == []
