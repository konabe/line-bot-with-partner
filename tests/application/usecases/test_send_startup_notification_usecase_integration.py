import os
from unittest.mock import MagicMock

from linebot.v3.messaging.models import PushMessageRequest

from src.application.usecases.send_startup_notification_usecase import (
    SendStartupNotificationUsecase,
)
from tests.support.mock_adapter import MockMessagingAdapter


def test_execute_with_admin_user_id_set(monkeypatch):
    """ADMIN_USER_IDが設定されている場合に起動通知が送信される結合テスト"""
    monkeypatch.setenv("ADMIN_USER_ID", "U123456789")
    monkeypatch.setenv("ADMIN_STARTUP_MESSAGE", "テストサーバーが起動しました")

    mock_line_adapter = MockMessagingAdapter()
    mock_line_adapter.push_message = MagicMock(return_value=True)
    mock_logger = MagicMock()

    usecase = SendStartupNotificationUsecase(mock_line_adapter, mock_logger)
    result = usecase.execute()

    assert result is True
    mock_line_adapter.push_message.assert_called_once()

    call_args = mock_line_adapter.push_message.call_args[0][0]
    assert isinstance(call_args, PushMessageRequest)
    assert call_args.to == "U123456789"
    assert len(call_args.messages) == 1
    assert call_args.messages[0].text == "テストサーバーが起動しました"

    mock_logger.info.assert_called_once()


def test_execute_without_admin_user_id(monkeypatch):
    """ADMIN_USER_IDが設定されていない場合に通知がスキップされる結合テスト"""
    monkeypatch.delenv("ADMIN_USER_ID", raising=False)

    mock_line_adapter = MockMessagingAdapter()
    mock_line_adapter.push_message = MagicMock()
    mock_logger = MagicMock()

    usecase = SendStartupNotificationUsecase(mock_line_adapter, mock_logger)
    result = usecase.execute()

    assert result is False
    mock_line_adapter.push_message.assert_not_called()
    mock_logger.debug.assert_called_once()


def test_execute_with_default_message(monkeypatch):
    """カスタムメッセージが設定されていない場合にデフォルトメッセージが使われる結合テスト"""
    monkeypatch.setenv("ADMIN_USER_ID", "U987654321")
    monkeypatch.delenv("ADMIN_STARTUP_MESSAGE", raising=False)

    mock_line_adapter = MockMessagingAdapter()
    mock_line_adapter.push_message = MagicMock(return_value=True)

    usecase = SendStartupNotificationUsecase(mock_line_adapter)
    result = usecase.execute()

    assert result is True
    call_args = mock_line_adapter.push_message.call_args[0][0]
    assert call_args.messages[0].text == "サーバーが起動しました。"


def test_execute_with_push_message_failure(monkeypatch):
    """push_messageが失敗した場合のエラーハンドリング結合テスト"""
    monkeypatch.setenv("ADMIN_USER_ID", "U123456789")

    mock_line_adapter = MockMessagingAdapter()
    mock_line_adapter.push_message = MagicMock(return_value=False)
    mock_logger = MagicMock()

    usecase = SendStartupNotificationUsecase(mock_line_adapter, mock_logger)
    result = usecase.execute()

    assert result is False
    mock_logger.error.assert_called_once()


def test_execute_with_exception(monkeypatch):
    """例外が発生した場合のエラーハンドリング結合テスト"""
    monkeypatch.setenv("ADMIN_USER_ID", "U123456789")

    mock_line_adapter = MockMessagingAdapter()
    mock_line_adapter.push_message = MagicMock(
        side_effect=RuntimeError("LINE API Error")
    )
    mock_logger = MagicMock()

    usecase = SendStartupNotificationUsecase(mock_line_adapter, mock_logger)
    result = usecase.execute()

    assert result is False
    mock_logger.error.assert_called_once()


def test_execute_with_none_return_from_push_message(monkeypatch):
    """push_messageがNoneを返した場合の後方互換性結合テスト"""
    monkeypatch.setenv("ADMIN_USER_ID", "U123456789")

    mock_line_adapter = MockMessagingAdapter()
    mock_line_adapter.push_message = MagicMock(return_value=None)
    mock_logger = MagicMock()

    usecase = SendStartupNotificationUsecase(mock_line_adapter, mock_logger)
    result = usecase.execute()

    assert result is True
    mock_logger.info.assert_called_once()
