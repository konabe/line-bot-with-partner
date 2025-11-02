from linebot.v3.messaging.models import ImageMessage, ReplyMessageRequest, TextMessage

from src.application.usecases.send_outfit_usecase import SendOutfitUsecase


class FakeEvent:
    def __init__(self):
        self.reply_token = "dummy"


def test_execute_success():
    sent = {}

    def fake_reply(req: ReplyMessageRequest):
        sent["req"] = req

    class FakeLineAdapter:
        def __init__(self, fn):
            self._fn = fn

        def reply_message(self, req):
            return self._fn(req)

    class FakeOpenAIAdapter:
        def generate_image(self, prompt: str) -> str:
            # return a dummy public URL
            return "https://example.com/outfit.png"

    usecase = SendOutfitUsecase(FakeLineAdapter(fake_reply), FakeOpenAIAdapter())
    ev = FakeEvent()
    usecase.execute(ev, "20度の服装")

    assert "req" in sent
    req = sent["req"]
    assert isinstance(req, ReplyMessageRequest)
    assert req.reply_token == ev.reply_token
    assert isinstance(req.messages[0], ImageMessage)
    assert req.messages[0].original_content_url == "https://example.com/outfit.png"


def test_execute_parse_failure():
    sent = {}

    def fake_reply(req: ReplyMessageRequest):
        sent["req"] = req

    class FakeLineAdapter:
        def __init__(self, fn):
            self._fn = fn

        def reply_message(self, req):
            return self._fn(req)

    class FakeOpenAIAdapter:
        def generate_image(self, prompt: str) -> str:
            return "https://example.com/outfit.png"

    usecase = SendOutfitUsecase(FakeLineAdapter(fake_reply), FakeOpenAIAdapter())
    ev = FakeEvent()
    usecase.execute(ev, "服装を教えて")

    assert "req" in sent
    req = sent["req"]
    assert isinstance(req.messages[0], TextMessage)
    assert "温度指定が見つかりませんでした" in req.messages[0].text


def test_execute_image_generation_failure():
    sent = {}

    def fake_reply(req: ReplyMessageRequest):
        sent["req"] = req

    class FakeLineAdapter:
        def __init__(self, fn):
            self._fn = fn

        def reply_message(self, req):
            return self._fn(req)

    class FakeOpenAIAdapterFail:
        def generate_image(self, prompt: str) -> str:
            return None

    usecase = SendOutfitUsecase(FakeLineAdapter(fake_reply), FakeOpenAIAdapterFail())
    ev = FakeEvent()
    usecase.execute(ev, "18度の服装")

    assert "req" in sent
    req = sent["req"]
    assert isinstance(req.messages[0], TextMessage)
    assert "画像の生成に失敗しました" in req.messages[0].text
