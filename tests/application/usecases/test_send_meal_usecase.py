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

    class FakeLineAdapter:
        def __init__(self, fn):
            self._fn = fn

        def reply_message(self, req):
            return self._fn(req)

    class FakeOpenAIAdapter:
        def get_chatgpt_meal_suggestion(self, return_request_id=False):
            result = fake_suggester()
            if return_request_id:
                return result, 12345  # ダミーのリクエストID
            return result

    usecase = SendMealUsecase(FakeLineAdapter(fake_reply), FakeOpenAIAdapter())
    ev = FakeEvent()
    usecase.execute(ev)

    assert "req" in sent
    req = sent["req"]
    assert isinstance(req, ReplyMessageRequest)
    assert req.reply_token == ev.reply_token
    assert isinstance(req.messages[0], TextMessage)
    assert "カレー" in req.messages[0].text
    # 2つ目のメッセージ（評価ボタン）があることを確認
    assert len(req.messages) == 2


def test_execute_failure():
    sent = {}

    def fake_reply(req: ReplyMessageRequest):
        sent["req"] = req

    def failing_suggester():
        raise RuntimeError("api error")

    class FakeLineAdapter:
        def __init__(self, fn):
            self._fn = fn

        def reply_message(self, req):
            return self._fn(req)

    class FakeOpenAIAdapterFail:
        def get_chatgpt_meal_suggestion(self, return_request_id=False):
            return failing_suggester()

    usecase = SendMealUsecase(FakeLineAdapter(fake_reply), FakeOpenAIAdapterFail())
    ev = FakeEvent()
    usecase.execute(ev)

    assert "req" in sent
    req = sent["req"]
    assert "OPENAI_API_KEY" in req.messages[0].text
