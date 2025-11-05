from unittest.mock import Mock

from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

from src.application.usecases.base_usecase import BaseUsecase


class FakeLineAdapter:
    def __init__(self):
        self.reply_message_calls = []

    def reply_message(self, req: ReplyMessageRequest):
        self.reply_message_calls.append(req)

    def push_message(self, req):
        pass

    def get_display_name_from_line_profile(self, user_id: str) -> str:
        return "TestUser"


def _make_fake_event(reply_token: str = "test_token"):
    event = Mock()
    event.reply_token = reply_token
    return event


class TestBaseUsecase:
    def test_validate_reply_token_with_valid_token(self):
        line_adapter = FakeLineAdapter()
        usecase = BaseUsecase(line_adapter)
        event = _make_fake_event("valid_token")

        result = usecase._validate_reply_token(event)

        assert result is True

    def test_validate_reply_token_with_none_token(self):
        line_adapter = FakeLineAdapter()
        usecase = BaseUsecase(line_adapter)
        event = _make_fake_event(None)

        result = usecase._validate_reply_token(event)

        assert result is False

    def test_send_text_reply(self):
        line_adapter = FakeLineAdapter()
        usecase = BaseUsecase(line_adapter)

        usecase._send_text_reply("test_token", "Hello, World!")

        assert len(line_adapter.reply_message_calls) == 1
        req = line_adapter.reply_message_calls[0]
        assert isinstance(req, ReplyMessageRequest)
        assert req.reply_token == "test_token"
        assert len(req.messages) == 1
        assert isinstance(req.messages[0], TextMessage)
        assert req.messages[0].text == "Hello, World!"

    def test_send_reply_with_multiple_messages(self):
        line_adapter = FakeLineAdapter()
        usecase = BaseUsecase(line_adapter)
        messages = [
            TextMessage(text="Message 1", quickReply=None, quoteToken=None),
            TextMessage(text="Message 2", quickReply=None, quoteToken=None),
        ]

        usecase._send_reply("test_token", messages)

        assert len(line_adapter.reply_message_calls) == 1
        req = line_adapter.reply_message_calls[0]
        assert req.reply_token == "test_token"
        assert len(req.messages) == 2
        assert req.messages[0].text == "Message 1"
        assert req.messages[1].text == "Message 2"

    def test_send_error_reply(self):
        line_adapter = FakeLineAdapter()
        usecase = BaseUsecase(line_adapter)

        usecase._send_error_reply("test_token", "Error occurred")

        assert len(line_adapter.reply_message_calls) == 1
        req = line_adapter.reply_message_calls[0]
        assert req.messages[0].text == "Error occurred"

    def test_logger_is_created(self):
        line_adapter = FakeLineAdapter()
        usecase = BaseUsecase(line_adapter)

        assert usecase._logger is not None
