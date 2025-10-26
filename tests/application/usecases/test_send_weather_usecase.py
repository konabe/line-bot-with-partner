from types import SimpleNamespace
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

from src.application.usecases.send_weather_usecase import SendWeatherUsecase


class FakeEvent:
    def __init__(self):
        self.reply_token = 'dummy'


def test_execute_with_location():
    replies = []

    def fake_safe_reply(req):
        replies.append(req)

    class FakeAdapter:
        def get_weather_text(self, loc):
            assert loc == '大阪'
            return '大阪: 晴れ'

    svc = SendWeatherUsecase(fake_safe_reply, FakeAdapter())
    evt = FakeEvent()
    svc.execute(evt, '大阪の天気')

    assert len(replies) == 1
    assert replies[0].messages[0].text == '大阪: 晴れ'


def test_execute_without_location():
    replies = []

    def fake_safe_reply(req):
        replies.append(req)

    class FakeAdapter2:
        def get_weather_text(self, loc):
            # default should be 東京
            assert loc == '東京'
            return '東京: 曇り'

    svc = SendWeatherUsecase(fake_safe_reply, FakeAdapter2())
    evt = FakeEvent()
    svc.execute(evt, '天気教えて')

    assert len(replies) == 1
    assert replies[0].messages[0].text == '東京: 曇り'


# --- multi-city tests merged below ---


class DummyEvent:
    def __init__(self):
        self.reply_token = 'token'


class MappingAdapter:
    def __init__(self, mapping):
        self.mapping = mapping

    def get_weather_text(self, location: str) -> str:
        return self.mapping.get(location, f"{location}の天気情報が見つかりませんでした。")


def test_plain_tenki_lists_multiple(monkeypatch):
    # configure env var with multiple cities
    monkeypatch.setenv('WEATHER_LOCATIONS', 'Tokyo, Osaka , Sapporo')

    mapping = {
        'Tokyo': 'Tokyo: 晴れ',
        'Osaka': 'Osaka: 曇り',
        'Sapporo': 'Sapporo: 雪'
    }
    sent = {}

    def fake_reply(req: ReplyMessageRequest):
        sent['req'] = req

    adapter = MappingAdapter(mapping)
    usecase = SendWeatherUsecase(fake_reply, adapter)
    ev = DummyEvent()
    usecase.execute(ev, '天気')

    assert 'req' in sent
    req = sent['req']
    assert isinstance(req, ReplyMessageRequest)
    assert req.reply_token == ev.reply_token
    # expect joined texts for each city
    assert 'Tokyo: 晴れ' in req.messages[0].text
    assert 'Osaka: 曇り' in req.messages[0].text
    assert 'Sapporo: 雪' in req.messages[0].text


def test_plain_tenki_no_env(monkeypatch):
    monkeypatch.delenv('WEATHER_LOCATIONS', raising=False)
    sent = {}

    def fake_reply(req: ReplyMessageRequest):
        sent['req'] = req

    adapter = MappingAdapter({})
    usecase = SendWeatherUsecase(fake_reply, adapter)
    ev = DummyEvent()
    usecase.execute(ev, '天気')

    assert 'req' in sent
    req = sent['req']
    assert 'WEATHER_LOCATIONS' in req.messages[0].text or '設定' in req.messages[0].text
