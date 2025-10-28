import pytest

from src.application.usecases.send_janken_options_usecase import (
    SendJankenOptionsUsecase,
)


def _make_event(reply_token="rtok"):
    class E:
        def __init__(self, reply_token):
            self.reply_token = reply_token

    return E(reply_token)


def test_execute_sends_janken_template():
    sent = []

    def fake_safe_reply(req):
        sent.append(req)

    svc = SendJankenOptionsUsecase(fake_safe_reply)
    event = _make_event("dummy-token")

    svc.execute(event)

    assert len(sent) == 1
    req = sent[0]
    assert getattr(req, "reply_token", None) == "dummy-token"

    # The first message should be a TemplateMessage with ButtonsTemplate and 3 PostbackAction
    msg = req.messages[0]
    assert hasattr(msg, "template")
    actions = msg.template.actions
    assert len(actions) == 3
    assert actions[0].data == "janken:✊"
    assert actions[1].data == "janken:✌️"
    assert actions[2].data == "janken:✋"


def test_execute_propagates_exception_from_safe_reply():
    def bad_safe_reply(_):
        raise RuntimeError("send failed")

    svc = SendJankenOptionsUsecase(bad_safe_reply)
    event = _make_event("t")

    with pytest.raises(RuntimeError):
        svc.execute(event)
