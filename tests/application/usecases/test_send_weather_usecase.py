from types import SimpleNamespace

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
