"""register_flask_routes のエラーハンドリング関数のテスト"""

import json
import time
from unittest.mock import Mock, patch

import pytest

from src.application.register_flask_routes import (
    _handle_general_error,
    _handle_signature_error,
    _is_duplicate_event,
    _processed_events,
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


class TestIsDuplicateEvent:
    """_is_duplicate_event 関数のテスト"""

    def setup_method(self):
        """各テスト前にキャッシュをクリア"""
        _processed_events.clear()

    def test_new_event_is_not_duplicate(self):
        """新しいイベントは重複していないこと"""
        body = json.dumps(
            {
                "events": [
                    {
                        "webhookEventId": "test_event_1",
                        "type": "message",
                    }
                ]
            }
        )

        result = _is_duplicate_event(body)

        assert result is False
        assert "test_event_1" in _processed_events

    def test_duplicate_event_is_detected(self):
        """同じwebhookEventIdは重複として検出されること"""
        body = json.dumps(
            {
                "events": [
                    {
                        "webhookEventId": "test_event_1",
                        "type": "message",
                    }
                ]
            }
        )

        # 1回目は重複ではない
        assert _is_duplicate_event(body) is False

        # 2回目は重複
        assert _is_duplicate_event(body) is True

    def test_multiple_events_in_single_request(self):
        """1つのリクエストに複数のイベントがある場合"""
        body = json.dumps(
            {
                "events": [
                    {"webhookEventId": "event_1", "type": "message"},
                    {"webhookEventId": "event_2", "type": "message"},
                ]
            }
        )

        assert _is_duplicate_event(body) is False
        assert "event_1" in _processed_events
        assert "event_2" in _processed_events

    def test_event_without_webhook_event_id(self):
        """webhookEventIdがないイベントは無視されること"""
        body = json.dumps({"events": [{"type": "message"}]})

        result = _is_duplicate_event(body)

        assert result is False
        assert len(_processed_events) == 0

    def test_expired_events_are_removed(self):
        """期限切れのイベントがキャッシュから削除されること"""
        # 過去のイベントを追加
        old_time = time.time() - 3700  # 1時間以上前
        _processed_events["old_event"] = old_time

        body = json.dumps(
            {"events": [{"webhookEventId": "new_event", "type": "message"}]}
        )

        _is_duplicate_event(body)

        # 古いイベントが削除されていること
        assert "old_event" not in _processed_events
        assert "new_event" in _processed_events

    def test_cache_size_limit(self):
        """キャッシュサイズが制限を超えると古いエントリが削除されること"""
        from src.application.register_flask_routes import _MAX_CACHE_SIZE

        # キャッシュを最大サイズまで埋める
        for i in range(_MAX_CACHE_SIZE):
            _processed_events[f"event_{i}"] = time.time()

        # 新しいイベントを追加
        body = json.dumps(
            {"events": [{"webhookEventId": "new_event", "type": "message"}]}
        )

        _is_duplicate_event(body)

        # キャッシュサイズが制限内であること
        assert len(_processed_events) <= _MAX_CACHE_SIZE
        # 最も古いエントリが削除されていること
        assert "event_0" not in _processed_events
        # 新しいイベントが追加されていること
        assert "new_event" in _processed_events

    def test_invalid_json_returns_false(self):
        """不正なJSONの場合はFalseを返すこと"""
        body = "invalid json"

        result = _is_duplicate_event(body)

        assert result is False

    def test_exception_during_processing_returns_false(self):
        """処理中に例外が発生した場合はFalseを返すこと"""
        body = json.dumps({"events": None})  # Noneをiterateしようとすると例外

        result = _is_duplicate_event(body)

        assert result is False
