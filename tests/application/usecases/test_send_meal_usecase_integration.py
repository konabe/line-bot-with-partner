from unittest.mock import MagicMock, Mock

from linebot.v3.messaging.models import (
    ButtonsTemplate,
    ReplyMessageRequest,
    TemplateMessage,
    TextMessage,
)

from src.application.usecases.send_meal_usecase import SendMealUsecase
from tests.support.mock_adapter import MockMessagingAdapter


def _make_fake_event():
    event = Mock()
    event.reply_token = "test_reply_token_123"
    return event


def test_execute_with_successful_meal_suggestion():
    """料理提案が正常に取得できる場合の結合テスト（PromptLayer未使用）"""
    mock_line_adapter = MockMessagingAdapter()
    mock_openai_adapter = MagicMock()
    mock_openai_adapter.get_chatgpt_meal_suggestion.return_value = "本日のおすすめ料理は麻婆豆腐です。"

    usecase = SendMealUsecase(mock_line_adapter, mock_openai_adapter)
    event = _make_fake_event()

    usecase.execute(event)

    mock_openai_adapter.get_chatgpt_meal_suggestion.assert_called_once_with(
        return_request_id=True
    )

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    assert isinstance(reply, ReplyMessageRequest)
    assert reply.reply_token == "test_reply_token_123"
    assert len(reply.messages) == 1
    assert isinstance(reply.messages[0], TextMessage)
    assert "麻婆豆腐" in reply.messages[0].text


def test_execute_with_promptlayer_request_id():
    """PromptLayerのリクエストIDが返された場合に評価ボタンが表示される結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_openai_adapter = MagicMock()
    mock_openai_adapter.get_chatgpt_meal_suggestion.return_value = (
        "本日のおすすめはカレーライスです。",
        12345,
    )

    usecase = SendMealUsecase(mock_line_adapter, mock_openai_adapter)
    event = _make_fake_event()

    usecase.execute(event)

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    assert isinstance(reply, ReplyMessageRequest)
    assert len(reply.messages) == 2

    assert isinstance(reply.messages[0], TextMessage)
    assert "カレーライス" in reply.messages[0].text

    assert isinstance(reply.messages[1], TemplateMessage)
    assert reply.messages[1].alt_text == "料理提案の評価をお願いします"
    assert isinstance(reply.messages[1].template, ButtonsTemplate)
    assert reply.messages[1].template.title == "評価"

    actions = reply.messages[1].template.actions
    assert len(actions) == 3
    assert actions[0].data == "meal_feedback:12345:100"
    assert actions[1].data == "meal_feedback:12345:50"
    assert actions[2].data == "meal_feedback:12345:0"


def test_execute_with_openai_exception():
    """OpenAIがエラーを返した場合のエラーメッセージ送信結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_openai_adapter = MagicMock()
    mock_openai_adapter.get_chatgpt_meal_suggestion.side_effect = RuntimeError(
        "API Error"
    )

    usecase = SendMealUsecase(mock_line_adapter, mock_openai_adapter)
    event = _make_fake_event()

    usecase.execute(event)

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    assert isinstance(reply, ReplyMessageRequest)
    assert len(reply.messages) == 1
    assert isinstance(reply.messages[0], TextMessage)
    assert "申し訳ない" in reply.messages[0].text or "失敗" in reply.messages[0].text


def test_execute_with_none_suggestion():
    """料理提案がNoneの場合のエラーメッセージ送信結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_openai_adapter = MagicMock()
    mock_openai_adapter.get_chatgpt_meal_suggestion.return_value = None

    usecase = SendMealUsecase(mock_line_adapter, mock_openai_adapter)
    event = _make_fake_event()

    usecase.execute(event)

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    assert len(reply.messages) == 1
    assert isinstance(reply.messages[0], TextMessage)
    assert "OPENAI_API_KEY" in reply.messages[0].text
