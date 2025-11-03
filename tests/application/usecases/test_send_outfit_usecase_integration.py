from unittest.mock import MagicMock

from linebot.v3.messaging.models import ImageMessage, ReplyMessageRequest, TextMessage

from src.application.usecases.send_outfit_usecase import SendOutfitUsecase
from tests.support.mock_adapter import MockMessagingAdapter


class FakeEvent:
    def __init__(self):
        self.reply_token = "test_reply_token_123"


def test_execute_with_valid_temperature():
    """有効な温度指定で服装画像が生成される結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_openai_adapter = MagicMock()
    mock_openai_adapter.generate_image_prompt.return_value = (
        "A stylish outfit for 20 degrees"
    )
    mock_openai_adapter.generate_image.return_value = (
        "https://example.com/outfit_image.png"
    )

    usecase = SendOutfitUsecase(mock_line_adapter, mock_openai_adapter)
    event = FakeEvent()

    usecase.execute(event, "20度の服装")

    mock_openai_adapter.generate_image_prompt.assert_called_once()
    mock_openai_adapter.generate_image.assert_called_once_with(
        "A stylish outfit for 20 degrees"
    )

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    assert isinstance(reply, ReplyMessageRequest)
    assert reply.reply_token == "test_reply_token_123"
    assert len(reply.messages) == 1
    assert isinstance(reply.messages[0], ImageMessage)
    assert (
        reply.messages[0].original_content_url == "https://example.com/outfit_image.png"
    )
    assert reply.messages[0].preview_image_url == "https://example.com/outfit_image.png"


def test_execute_with_invalid_temperature_format():
    """温度指定が不正な場合のエラーメッセージ送信結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_openai_adapter = MagicMock()

    usecase = SendOutfitUsecase(mock_line_adapter, mock_openai_adapter)
    event = FakeEvent()

    usecase.execute(event, "服装を教えて")

    mock_openai_adapter.generate_image_prompt.assert_not_called()
    mock_openai_adapter.generate_image.assert_not_called()

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    assert isinstance(reply, ReplyMessageRequest)
    assert len(reply.messages) == 1
    assert isinstance(reply.messages[0], TextMessage)
    assert "温度指定が見つかりませんでした" in reply.messages[0].text


def test_execute_with_image_generation_failure():
    """画像生成が失敗した場合のエラーメッセージ送信結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_openai_adapter = MagicMock()
    mock_openai_adapter.generate_image_prompt.return_value = "Outfit prompt"
    mock_openai_adapter.generate_image.side_effect = RuntimeError("Image API error")

    usecase = SendOutfitUsecase(mock_line_adapter, mock_openai_adapter)
    event = FakeEvent()

    usecase.execute(event, "25度の服装")

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    assert isinstance(reply, ReplyMessageRequest)
    assert len(reply.messages) == 1
    assert isinstance(reply.messages[0], TextMessage)
    assert "失敗" in reply.messages[0].text


def test_execute_with_various_temperatures():
    """様々な温度指定でも正常に処理される結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_openai_adapter = MagicMock()
    mock_openai_adapter.generate_image_prompt.return_value = "Outfit prompt"
    mock_openai_adapter.generate_image.return_value = "https://example.com/image.png"

    usecase = SendOutfitUsecase(mock_line_adapter, mock_openai_adapter)

    test_cases = ["5度の服装", "15 度の服装", "30度の服装", "0度の服装"]

    for idx, test_input in enumerate(test_cases):
        event = FakeEvent()
        event.reply_token = f"token_{idx}"
        usecase.execute(event, test_input)

    replies = mock_line_adapter.get_replies()
    assert len(replies) == len(test_cases)

    for reply in replies:
        assert isinstance(reply.messages[0], ImageMessage)
