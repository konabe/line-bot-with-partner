from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

from src.application.usecases.send_meal_usecase import SendMealUsecase


class FakeEvent:
    def __init__(self):
        self.reply_token = "dummy"


def test_execute_success():
    sent = {}

    def fake_reply(req: ReplyMessageRequest):
        sent["req"] = req

    def fake_suggester():
        return "今日のご飯: カレー（簡単レシピ付き）"

    usecase = SendMealUsecase(fake_reply, fake_suggester)
    ev = FakeEvent()
    usecase.execute(ev)

    assert "req" in sent
    req = sent["req"]
    assert isinstance(req, ReplyMessageRequest)
    assert req.reply_token == ev.reply_token
    assert isinstance(req.messages[0], TextMessage)
    assert "カレー" in req.messages[0].text


def test_execute_failure():
    sent = {}

    def fake_reply(req: ReplyMessageRequest):
        sent["req"] = req

    def failing_suggester():
        raise RuntimeError("api error")

    usecase = SendMealUsecase(fake_reply, failing_suggester)
    ev = FakeEvent()
    usecase.execute(ev)

    assert "req" in sent
    req = sent["req"]
    assert "OPENAI_API_KEY" in req.messages[0].text
