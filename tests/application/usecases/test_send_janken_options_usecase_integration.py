from linebot.v3.messaging.models import (
    ButtonsTemplate,
    PostbackAction,
    ReplyMessageRequest,
    TemplateMessage,
)

from src.application.usecases.send_janken_options_usecase import (
    SendJankenOptionsUsecase,
)
from tests.support.mock_adapter import MockMessagingAdapter


class FakeEvent:
    def __init__(self):
        self.reply_token = "test_reply_token_123"


def test_execute_sends_janken_template():
    """じゃんけん選択肢が正常に送信される結合テスト"""
    mock_line_adapter = MockMessagingAdapter()

    usecase = SendJankenOptionsUsecase(mock_line_adapter)
    event = FakeEvent()

    usecase.execute(event)

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    assert isinstance(reply, ReplyMessageRequest)
    assert reply.reply_token == "test_reply_token_123"
    assert len(reply.messages) == 1

    message = reply.messages[0]
    assert isinstance(message, TemplateMessage)
    assert message.alt_text == "じゃんけんしましょう！"
    assert isinstance(message.template, ButtonsTemplate)
    assert message.template.title == "じゃんけん"
    assert message.template.text == "どれを出しますか？"
    assert len(message.template.actions) == 3

    for action in message.template.actions:
        assert isinstance(action, PostbackAction)
        assert action.data is not None
        assert action.data.startswith("janken:")

    labels = [action.label for action in message.template.actions]
    assert "✊ グー" in labels
    assert "✌️ チョキ" in labels
    assert "✋ パー" in labels


def test_execute_multiple_times():
    """複数回実行しても正常に動作する結合テスト"""
    mock_line_adapter = MockMessagingAdapter()

    usecase = SendJankenOptionsUsecase(mock_line_adapter)
    event1 = FakeEvent()
    event2 = FakeEvent()
    event2.reply_token = "test_reply_token_456"

    usecase.execute(event1)
    usecase.execute(event2)

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 2
    assert replies[0].reply_token == "test_reply_token_123"
    assert replies[1].reply_token == "test_reply_token_456"
