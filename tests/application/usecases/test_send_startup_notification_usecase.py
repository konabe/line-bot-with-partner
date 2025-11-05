import os
from unittest.mock import Mock

import pytest
from linebot.v3.messaging.models import PushMessageRequest

from src.application.usecases.send_startup_notification_usecase import (
    SendStartupNotificationUsecase,
)


def test_send_startup_notification_success(monkeypatch):
    """起動通知送信の成功ケース"""
    # 環境変数を設定
    monkeypatch.setenv("ADMIN_USER_ID", "test_admin_id")
    monkeypatch.setenv("ADMIN_STARTUP_MESSAGE", "テストメッセージ")

    # モックLINEアダプター
    mock_line_adapter = Mock()
    mock_line_adapter.push_message.return_value = True

    # モックロガー
    mock_logger = Mock()

    # ユースケースを実行
    usecase = SendStartupNotificationUsecase(mock_line_adapter, mock_logger)
    result = usecase.execute()

    # 検証
    assert result is True
    mock_line_adapter.push_message.assert_called_once()

    # push_message の引数を確認
    call_args = mock_line_adapter.push_message.call_args[0][0]
    assert isinstance(call_args, PushMessageRequest)
    assert call_args.to == "test_admin_id"
    assert call_args.messages[0].text == "テストメッセージ"

    mock_logger.info.assert_called_once_with(
        "startup notification sent to admin test_admin_id"
    )


def test_send_startup_notification_no_admin_id(monkeypatch):
    """ADMIN_USER_IDが設定されていない場合"""
    # 環境変数をクリア
    monkeypatch.delenv("ADMIN_USER_ID", raising=False)

    mock_line_adapter = Mock()
    mock_logger = Mock()

    usecase = SendStartupNotificationUsecase(mock_line_adapter, mock_logger)
    result = usecase.execute()

    # 検証
    assert result is False
    mock_line_adapter.push_message.assert_not_called()
    mock_logger.debug.assert_called_once_with(
        "ADMIN_USER_ID not set; skipping startup notification"
    )


def test_send_startup_notification_default_message(monkeypatch):
    """デフォルトメッセージを使用する場合"""
    monkeypatch.setenv("ADMIN_USER_ID", "test_admin_id")
    monkeypatch.delenv("ADMIN_STARTUP_MESSAGE", raising=False)

    mock_line_adapter = Mock()
    mock_line_adapter.push_message.return_value = True
    mock_logger = Mock()

    usecase = SendStartupNotificationUsecase(mock_line_adapter, mock_logger)
    result = usecase.execute()

    # 検証
    assert result is True
    call_args = mock_line_adapter.push_message.call_args[0][0]
    assert call_args.messages[0].text == "サーバーが起動しました。"


def test_send_startup_notification_failure(monkeypatch):
    """メッセージ送信が失敗した場合"""
    monkeypatch.setenv("ADMIN_USER_ID", "test_admin_id")

    mock_line_adapter = Mock()
    mock_line_adapter.push_message.return_value = False
    mock_logger = Mock()

    usecase = SendStartupNotificationUsecase(mock_line_adapter, mock_logger)
    result = usecase.execute()

    # 検証
    assert result is False
    # エラーメッセージには例外のメッセージが含まれる
    mock_logger.error.assert_called_once()
    error_message = mock_logger.error.call_args[0][0]
    assert "startup notification failed with exception" in error_message
    assert "failed to send startup notification to admin test_admin_id" in error_message


def test_send_startup_notification_exception(monkeypatch):
    """例外が発生した場合"""
    monkeypatch.setenv("ADMIN_USER_ID", "test_admin_id")

    mock_line_adapter = Mock()
    mock_line_adapter.push_message.side_effect = Exception("Connection error")
    mock_logger = Mock()

    usecase = SendStartupNotificationUsecase(mock_line_adapter, mock_logger)
    result = usecase.execute()

    # 検証
    assert result is False
    mock_logger.error.assert_called_once_with(
        "startup notification failed with exception: Connection error"
    )


def test_send_startup_notification_none_return(monkeypatch):
    """push_messageがNoneを返す場合（後方互換性）"""
    monkeypatch.setenv("ADMIN_USER_ID", "test_admin_id")

    mock_line_adapter = Mock()
    mock_line_adapter.push_message.return_value = None
    mock_logger = Mock()

    usecase = SendStartupNotificationUsecase(mock_line_adapter, mock_logger)
    result = usecase.execute()

    # 検証
    assert result is True  # Noneは成功として扱われる
    mock_logger.info.assert_called_once_with(
        "startup notification sent to admin test_admin_id"
    )
