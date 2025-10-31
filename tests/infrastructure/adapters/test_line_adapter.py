"""LineMessagingAdapter のテスト"""

from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.adapters.line_adapter import LineMessagingAdapter


class TestLineMessagingAdapter:
    def test_init_with_logger(self):
        """loggerを指定してインスタンス化できること"""
        mock_logger = MagicMock()
        adapter = LineMessagingAdapter(logger=mock_logger)

        assert adapter.logger == mock_logger
        assert adapter.messaging_api is None

    def test_init_without_logger(self):
        """loggerなしでインスタンス化でき、デフォルトloggerが設定されること"""
        adapter = LineMessagingAdapter()

        assert adapter.logger is not None
        assert adapter.messaging_api is None

    @patch("src.infrastructure.adapters.line_adapter.MessagingApi")
    @patch("src.infrastructure.adapters.line_adapter.ApiClient")
    @patch("src.infrastructure.adapters.line_adapter.Configuration")
    def test_init_success(self, mock_config, mock_api_client, mock_messaging_api):
        """正常にMessagingAPIを初期化できること"""
        mock_logger = MagicMock()
        adapter = LineMessagingAdapter(logger=mock_logger)

        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance
        mock_api_client_instance = MagicMock()
        mock_api_client.return_value = mock_api_client_instance
        mock_messaging_api_instance = MagicMock()
        mock_messaging_api.return_value = mock_messaging_api_instance

        adapter.init("test_access_token")

        mock_config.assert_called_once_with(access_token="test_access_token")
        mock_api_client.assert_called_once_with(configuration=mock_config_instance)
        mock_messaging_api.assert_called_once_with(mock_api_client_instance)
        assert adapter.messaging_api == mock_messaging_api_instance

    @patch("src.infrastructure.adapters.line_adapter.Configuration")
    def test_init_import_error(self, mock_config):
        """インポートエラー時にmessaging_apiがNoneのままであること"""
        mock_logger = MagicMock()
        adapter = LineMessagingAdapter(logger=mock_logger)

        mock_config.side_effect = Exception("Module not found")
        adapter.init("test_access_token")

        assert adapter.messaging_api is None
        mock_logger.error.assert_called_once()

    def test_reply_message_not_initialized(self):
        """messaging_apiが初期化されていない場合、warningログを出力すること"""
        mock_logger = MagicMock()
        adapter = LineMessagingAdapter(logger=mock_logger)

        mock_request = MagicMock()
        adapter.reply_message(mock_request)

        mock_logger.warning.assert_called_once_with(
            "messaging_api is not initialized; skipping reply_message"
        )

    def test_reply_message_success(self):
        """正常にreply_messageを呼び出せること"""
        mock_logger = MagicMock()
        adapter = LineMessagingAdapter(logger=mock_logger)

        mock_messaging_api = MagicMock()
        adapter.messaging_api = mock_messaging_api

        mock_request = MagicMock()
        mock_request.to_dict.return_value = {"test": "data"}

        adapter.reply_message(mock_request)

        mock_messaging_api.reply_message.assert_called_once_with(mock_request)
        mock_logger.debug.assert_called()

    @patch("linebot.v3.messaging.models.ReplyMessageRequest.parse_obj")
    def test_reply_message_error(self, mock_parse_obj):
        """reply_message中にエラーが発生した場合、例外を再送出すること"""
        mock_logger = MagicMock()
        adapter = LineMessagingAdapter(logger=mock_logger)

        mock_messaging_api = MagicMock()
        mock_messaging_api.reply_message.side_effect = Exception("API Error")
        adapter.messaging_api = mock_messaging_api

        mock_request = MagicMock()
        mock_request.to_dict.return_value = {"test": "data"}
        mock_parse_obj.side_effect = Exception("Parse Error")

        with pytest.raises(Exception):
            adapter.reply_message(mock_request)

        mock_logger.error.assert_called()

    def test_push_message_not_initialized(self):
        """messaging_apiが初期化されていない場合、warningログを出力すること"""
        mock_logger = MagicMock()
        adapter = LineMessagingAdapter(logger=mock_logger)

        mock_request = MagicMock()
        adapter.push_message(mock_request)

        mock_logger.warning.assert_called_once_with(
            "messaging_api is not initialized; skipping push_message"
        )

    def test_push_message_success(self):
        """正常にpush_messageを呼び出せること"""
        mock_logger = MagicMock()
        adapter = LineMessagingAdapter(logger=mock_logger)

        mock_messaging_api = MagicMock()
        adapter.messaging_api = mock_messaging_api

        mock_request = MagicMock()
        mock_request.to_dict.return_value = {"test": "data"}

        adapter.push_message(mock_request)

        mock_messaging_api.push_message.assert_called_once_with(mock_request)
        mock_logger.debug.assert_called()

    @patch("linebot.v3.messaging.models.PushMessageRequest.parse_obj")
    def test_push_message_error(self, mock_parse_obj):
        """push_message中にエラーが発生した場合、例外を再送出すること"""
        mock_logger = MagicMock()
        adapter = LineMessagingAdapter(logger=mock_logger)

        mock_messaging_api = MagicMock()
        mock_messaging_api.push_message.side_effect = Exception("API Error")
        adapter.messaging_api = mock_messaging_api

        mock_request = MagicMock()
        mock_request.to_dict.return_value = {"test": "data"}
        mock_parse_obj.side_effect = Exception("Parse Error")

        with pytest.raises(Exception):
            adapter.push_message(mock_request)

        mock_logger.error.assert_called()

    def test_get_display_name_success(self):
        """正常にユーザー名を取得できること"""
        mock_logger = MagicMock()
        adapter = LineMessagingAdapter(logger=mock_logger)

        mock_messaging_api = MagicMock()
        mock_profile = MagicMock()
        mock_profile.display_name = "Test User"
        mock_messaging_api.get_profile.return_value = mock_profile
        adapter.messaging_api = mock_messaging_api

        result = adapter.get_display_name_from_line_profile("user123")

        assert result == "Test User"
        mock_messaging_api.get_profile.assert_called_once_with("user123")

    def test_get_display_name_not_initialized(self):
        """messaging_apiが初期化されていない場合、Noneを返すこと"""
        mock_logger = MagicMock()
        adapter = LineMessagingAdapter(logger=mock_logger)

        result = adapter.get_display_name_from_line_profile("user123")

        assert result is None
        mock_logger.debug.assert_called_once()

    def test_get_display_name_empty_user_id(self):
        """user_idが空の場合、Noneを返すこと"""
        mock_logger = MagicMock()
        adapter = LineMessagingAdapter(logger=mock_logger)

        mock_messaging_api = MagicMock()
        adapter.messaging_api = mock_messaging_api

        result = adapter.get_display_name_from_line_profile("")

        assert result is None
        mock_logger.debug.assert_called_once()
        mock_messaging_api.get_profile.assert_not_called()

    def test_get_display_name_api_error(self):
        """API呼び出し中にエラーが発生した場合、Noneを返すこと"""
        mock_logger = MagicMock()
        adapter = LineMessagingAdapter(logger=mock_logger)

        mock_messaging_api = MagicMock()
        mock_messaging_api.get_profile.side_effect = Exception("API error")
        adapter.messaging_api = mock_messaging_api

        result = adapter.get_display_name_from_line_profile("user123")

        assert result is None
        mock_logger.error.assert_called_once()
