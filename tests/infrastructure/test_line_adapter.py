import types

from src.infrastructure.line_adapter import LineMessagingAdapter


class FakeAPI:
    def __init__(self):
        self.last = None

    def reply_message(self, payload):
        # capture payload as-is
        self.last = payload


def test_reply_with_dict_flex_payload():
    adapter = LineMessagingAdapter()
    adapter.messaging_api = FakeAPI()

    payload = {
        'replyToken': 't',
        'messages': [{
            'type': 'flex',
            'altText': 'alt',
            'contents': {'type': 'bubble', 'body': {'type': 'box', 'layout': 'vertical', 'contents': []}}
        }]
    }

    adapter.reply_message(payload)
    assert isinstance(adapter.messaging_api.last, dict)
    assert adapter.messaging_api.last['messages'][0]['altText'] == 'alt'


def test_reply_with_sdk_model_like_object():
    adapter = LineMessagingAdapter()
    adapter.messaging_api = FakeAPI()

    class SDKLike:
        def __init__(self):
            pass

        def to_dict(self):
            return {'replyToken': 't2', 'messages': [{'type': 'text', 'text': 'hi'}]}

    adapter.reply_message(SDKLike())
    assert isinstance(adapter.messaging_api.last, dict)
    assert adapter.messaging_api.last['messages'][0]['text'] == 'hi'
