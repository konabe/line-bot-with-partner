from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

from src.application.usecases.send_chat_response_usecase import SendChatResponseUsecase


class FakeEvent:
    def __init__(self):
        self.reply_token = "dummy"


def test_execute_success():
    sent = {}

    def fake_reply(req: ReplyMessageRequest):
        sent["req"] = req

    def fake_chatgpt(msg: str):
        return "応答: " + msg

    usecase = SendChatResponseUsecase(fake_reply, fake_chatgpt)
    ev = FakeEvent()
    usecase.execute(ev, "こんにちは")

    assert "req" in sent
    req = sent["req"]
    assert isinstance(req, ReplyMessageRequest)
    assert req.reply_token == ev.reply_token
    assert isinstance(req.messages[0], TextMessage)
    assert "応答: こんにちは" in req.messages[0].text


def test_execute_failure():
    sent = {}

    def fake_reply(req: ReplyMessageRequest):
        sent["req"] = req

    def failing_chatgpt(msg: str):
        raise RuntimeError("api error")

    usecase = SendChatResponseUsecase(fake_reply, failing_chatgpt)
    ev = FakeEvent()
    usecase.execute(ev, "こんにちは")

    assert "req" in sent
    req = sent["req"]
    assert "OPENAI_API_KEY" in req.messages[0].text
