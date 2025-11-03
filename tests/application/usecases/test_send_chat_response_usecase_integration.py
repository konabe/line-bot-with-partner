from unittest.mock import MagicMock

from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

from src.application.usecases.send_chat_response_usecase import SendChatResponseUsecase
from tests.support.mock_adapter import MockMessagingAdapter


class FakeEvent:
    def __init__(self):
        self.reply_token = "test_reply_token_123"


def test_execute_with_successful_openai_response():
    """OpenAIから正常なレスポンスが返る場合の結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_openai_adapter = MagicMock()
    mock_openai_adapter.get_chatgpt_response.return_value = "こんにちは!元気ですか?"

    usecase = SendChatResponseUsecase(mock_line_adapter, mock_openai_adapter)
    event = FakeEvent()

    usecase.execute(event, "こんにちは")

    mock_openai_adapter.get_chatgpt_response.assert_called_once_with("こんにちは")

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    assert isinstance(reply, ReplyMessageRequest)
    assert reply.reply_token == "test_reply_token_123"
    assert len(reply.messages) == 1
    assert isinstance(reply.messages[0], TextMessage)
    assert "こんにちは!元気ですか?" in reply.messages[0].text


def test_execute_with_openai_exception():
    """OpenAIがエラーを返した場合でもエラーメッセージが送信される結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_openai_adapter = MagicMock()
    mock_openai_adapter.get_chatgpt_response.side_effect = RuntimeError(
        "OpenAI API error"
    )

    usecase = SendChatResponseUsecase(mock_line_adapter, mock_openai_adapter)
    event = FakeEvent()

    usecase.execute(event, "テスト")

    mock_openai_adapter.get_chatgpt_response.assert_called_once_with("テスト")

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    assert isinstance(reply, ReplyMessageRequest)
    assert reply.reply_token == "test_reply_token_123"
    assert len(reply.messages) == 1
    assert isinstance(reply.messages[0], TextMessage)
    assert "申し訳ない" in reply.messages[0].text or "できませんでした" in reply.messages[0].text


def test_execute_with_long_user_message():
    """長いユーザーメッセージでも正常に処理できる結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_openai_adapter = MagicMock()
    long_message = "これは長いメッセージです。" * 50
    mock_openai_adapter.get_chatgpt_response.return_value = "了解しました。"

    usecase = SendChatResponseUsecase(mock_line_adapter, mock_openai_adapter)
    event = FakeEvent()

    usecase.execute(event, long_message)

    mock_openai_adapter.get_chatgpt_response.assert_called_once_with(long_message)

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    assert isinstance(replies[0], ReplyMessageRequest)
