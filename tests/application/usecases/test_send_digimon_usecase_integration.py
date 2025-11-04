from unittest.mock import MagicMock, Mock

from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

from src.application.usecases.send_digimon_usecase import SendDigimonUsecase
from src.domain.models.digimon_info import DigimonInfo
from tests.support.mock_adapter import MockMessagingAdapter


def _make_fake_event():
    event = Mock()
    event.reply_token = "test_reply_token_123"
    return event


def test_execute_with_successful_digimon_info():
    """デジモン情報が正常に取得できる場合の結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_digimon_adapter = MagicMock()

    digimon_info = DigimonInfo(
        id=1,
        name="アグモン",
        level="成長期",
        image_url="https://example.com/agumon.png",
    )
    mock_digimon_adapter.get_random_digimon_info.return_value = digimon_info

    usecase = SendDigimonUsecase(mock_line_adapter, mock_digimon_adapter)
    event = _make_fake_event()

    usecase.execute(event)

    mock_digimon_adapter.get_random_digimon_info.assert_called_once()

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    assert isinstance(reply, ReplyMessageRequest)
    assert reply.reply_token == "test_reply_token_123"
    assert len(reply.messages) == 1


def test_execute_with_no_digimon_info():
    """デジモン情報が取得できない場合のエラーハンドリング結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_digimon_adapter = MagicMock()
    mock_digimon_adapter.get_random_digimon_info.return_value = None

    usecase = SendDigimonUsecase(mock_line_adapter, mock_digimon_adapter)
    event = _make_fake_event()

    usecase.execute(event)

    mock_digimon_adapter.get_random_digimon_info.assert_called_once()

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    assert isinstance(reply, ReplyMessageRequest)
    assert reply.reply_token == "test_reply_token_123"
    assert len(reply.messages) == 1
    assert isinstance(reply.messages[0], TextMessage)
    assert "失敗" in reply.messages[0].text


def test_execute_with_digimon_adapter_exception():
    """デジモンアダプターで例外が発生した場合の結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_digimon_adapter = MagicMock()
    mock_digimon_adapter.get_random_digimon_info.side_effect = RuntimeError("API Error")

    usecase = SendDigimonUsecase(mock_line_adapter, mock_digimon_adapter)
    event = _make_fake_event()

    try:
        usecase.execute(event)
    except RuntimeError:
        pass

    mock_digimon_adapter.get_random_digimon_info.assert_called_once()
