"""register_flask_routes のエラーハンドリング関数のテスト"""

import json
from unittest.mock import Mock, patch

import pytest

from src.application.register_flask_routes import (
    _handle_general_error,
    _handle_signature_error,
)


class FakeLineAdapter:
    """テスト用 LINE アダプタ"""

    def __init__(self):
        self.reply_message_calls = []

    def reply_message(self, req):
        self.reply_message_calls.append(req)


class TestHandleSignatureError:
    """_handle_signature_error 関数のテスト"""

    def test_handle_signature_error_sends_error_message(self):
        """署名エラー時にエラーメッセージを送信すること"""
        line_adapter = FakeLineAdapter()

        body = json.dumps(
            {
                "events": [
                    {
                        "replyToken": "test_reply_token",
                        "type": "message",
                        "message": {"type": "text", "text": "test"},
                    }
                ]
            }
        )

        _handle_signature_error(body, line_adapter)

        # reply_message が1回呼ばれていることを確認
        assert len(line_adapter.reply_message_calls) == 1

        # 送信されたメッセージを確認
        req = line_adapter.reply_message_calls[0]
        assert req.reply_token == "test_reply_token"
        assert len(req.messages) == 1
        assert "署名検証に失敗" in req.messages[0].text

    def test_handle_signature_error_with_multiple_events(self):
        """複数イベントがある場合、それぞれにエラーメッセージを送信すること"""
        line_adapter = FakeLineAdapter()

        body = json.dumps(
            {
                "events": [
                    {"replyToken": "token1", "type": "message"},
                    {"replyToken": "token2", "type": "message"},
                ]
            }
        )

        _handle_signature_error(body, line_adapter)

        # reply_message が2回呼ばれていることを確認
        assert len(line_adapter.reply_message_calls) == 2
        assert line_adapter.reply_message_calls[0].reply_token == "token1"
        assert line_adapter.reply_message_calls[1].reply_token == "token2"

    def test_handle_signature_error_with_no_reply_token(self):
        """replyToken がない場合は何も送信しないこと"""
        line_adapter = FakeLineAdapter()

        body = json.dumps({"events": [{"type": "message"}]})

        _handle_signature_error(body, line_adapter)

        # reply_message が呼ばれていないことを確認
        assert len(line_adapter.reply_message_calls) == 0

    def test_handle_signature_error_with_invalid_json(self):
        """不正な JSON の場合、例外をキャッチして何も送信しないこと"""
        line_adapter = FakeLineAdapter()

        body = "invalid json"

        # 例外が発生しないことを確認
        _handle_signature_error(body, line_adapter)

        # reply_message が呼ばれていないことを確認
        assert len(line_adapter.reply_message_calls) == 0

    def test_handle_signature_error_when_reply_fails(self):
        """reply_message が失敗した場合、例外をキャッチすること"""

        class FailingLineAdapter:
            def reply_message(self, req):
                raise Exception("Reply failed")

        line_adapter = FailingLineAdapter()

        body = json.dumps({"events": [{"replyToken": "test_token"}]})

        # 例外が発生しないことを確認（内部でキャッチされる）
        _handle_signature_error(body, line_adapter)


class TestHandleGeneralError:
    """_handle_general_error 関数のテスト"""

    def test_handle_general_error_sends_error_message(self):
        """一般エラー時にエラーメッセージを送信すること"""
        line_adapter = FakeLineAdapter()

        body = json.dumps(
            {
                "events": [
                    {
                        "replyToken": "test_reply_token",
                        "type": "message",
                        "message": {"type": "text", "text": "test"},
                    }
                ]
            }
        )

        _handle_general_error(body, line_adapter)

        # reply_message が1回呼ばれていることを確認
        assert len(line_adapter.reply_message_calls) == 1

        # 送信されたメッセージを確認
        req = line_adapter.reply_message_calls[0]
        assert req.reply_token == "test_reply_token"
        assert len(req.messages) == 1
        assert "障害が発生" in req.messages[0].text

    def test_handle_general_error_with_multiple_events(self):
        """複数イベントがある場合、それぞれにエラーメッセージを送信すること"""
        line_adapter = FakeLineAdapter()

        body = json.dumps(
            {
                "events": [
                    {"replyToken": "token1", "type": "message"},
                    {"replyToken": "token2", "type": "message"},
                ]
            }
        )

        _handle_general_error(body, line_adapter)

        # reply_message が2回呼ばれていることを確認
        assert len(line_adapter.reply_message_calls) == 2
        assert line_adapter.reply_message_calls[0].reply_token == "token1"
        assert line_adapter.reply_message_calls[1].reply_token == "token2"

    def test_handle_general_error_with_no_reply_token(self):
        """replyToken がない場合は何も送信しないこと"""
        line_adapter = FakeLineAdapter()

        body = json.dumps({"events": [{"type": "message"}]})

        _handle_general_error(body, line_adapter)

        # reply_message が呼ばれていないことを確認
        assert len(line_adapter.reply_message_calls) == 0

    def test_handle_general_error_with_invalid_json(self):
        """不正な JSON の場合、例外をキャッチして何も送信しないこと"""
        line_adapter = FakeLineAdapter()

        body = "invalid json"

        # 例外が発生しないことを確認
        _handle_general_error(body, line_adapter)

        # reply_message が呼ばれていないことを確認
        assert len(line_adapter.reply_message_calls) == 0

    def test_handle_general_error_when_reply_fails(self):
        """reply_message が失敗した場合、例外をキャッチすること"""

        class FailingLineAdapter:
            def reply_message(self, req):
                raise Exception("Reply failed")

        line_adapter = FailingLineAdapter()

        body = json.dumps({"events": [{"replyToken": "test_token"}]})

        # 例外が発生しないことを確認（内部でキャッチされる）
        _handle_general_error(body, line_adapter)
