from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

from src.application.usecases.send_chat_response_usecase import SendChatResponseUsecase


class FakeEvent:
    def __init__(self):
        self.reply_token = "dummy"


def test_execute_success():
    sent = {}

    class FakeLineAdapter:
        def reply_message(self, req: ReplyMessageRequest):
            sent["req"] = req

    class FakeOpenAI:
        def get_chatgpt_response(self, user_message: str) -> str:
            return "応答: " + user_message

    usecase = SendChatResponseUsecase(FakeLineAdapter(), FakeOpenAI())
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

    class FakeLineAdapter:
        def reply_message(self, req: ReplyMessageRequest):
            sent["req"] = req

    class FailingOpenAI:
        def get_chatgpt_response(self, user_message: str) -> str:
            raise RuntimeError("api error")

    usecase = SendChatResponseUsecase(FakeLineAdapter(), FailingOpenAI())
    ev = FakeEvent()
    usecase.execute(ev, "こんにちは")

    assert "req" in sent
    req = sent["req"]
    assert "OPENAI_API_KEY" in req.messages[0].text
