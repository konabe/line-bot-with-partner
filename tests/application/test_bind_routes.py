"""bind_routes の単体テスト"""

from unittest.mock import MagicMock, Mock

import pytest

from src.application.bind_routes import bind_routes


class FakeLineAdapter:
    """テスト用 LINE アダプタ"""

    def __init__(self):
        self.reply_message_calls = []

    def reply_message(self, req):
        self.reply_message_calls.append(req)


class FakeWebhookHandler:
    """テスト用 Webhook ハンドラ"""

    def __init__(self):
        self.decorators = []

    def add(self, event_type):
        """デコレータを保存して返す"""

        def decorator(func):
            self.decorators.append((event_type, func))
            return func

        return decorator


class FakeLogger:
    """テスト用ロガー"""

    def __init__(self):
        self.debug_logs = []
        self.error_logs = []
        self.info_logs = []

    def debug(self, msg, *args):
        self.debug_logs.append(msg)

    def error(self, msg, *args):
        self.error_logs.append(msg)

    def info(self, msg, *args):
        self.info_logs.append(msg)


class TestBindRoutes:
    """bind_routes 関数のテスト"""

    def test_bind_routes_registers_message_and_postback_handlers(self, monkeypatch):
        """bind_routes が MessageEvent と PostbackEvent のハンドラを登録すること"""
        # Flask app のモック
        fake_app = Mock()
        fake_app.route = Mock()

        # WebhookHandler のモック
        fake_handler = FakeWebhookHandler()

        # LINE アダプタのモック
        fake_line_adapter = FakeLineAdapter()

        # Logger のモック
        fake_logger = FakeLogger()

        # OpenAI 環境変数を設定（bind_routes 内で使用される）
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # bind_routes を実行
        bind_routes(fake_app, fake_handler, fake_line_adapter, fake_logger)

        # 2つのハンドラ（MessageEvent, PostbackEvent）が登録されていることを確認
        assert len(fake_handler.decorators) == 2

        # デコレータの型を確認
        from linebot.v3.webhooks.models.message_event import MessageEvent
        from linebot.v3.webhooks.models.postback_event import PostbackEvent

        event_types = [decorator[0] for decorator in fake_handler.decorators]
        assert MessageEvent in event_types
        assert PostbackEvent in event_types

    def test_bind_routes_uses_provided_line_adapter(self, monkeypatch):
        """bind_routes が提供された line_adapter を使用すること"""
        fake_app = Mock()
        fake_app.route = Mock()

        fake_handler = FakeWebhookHandler()
        provided_adapter = FakeLineAdapter()
        fake_logger = FakeLogger()

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # 提供した line_adapter を使用
        bind_routes(fake_app, fake_handler, provided_adapter, fake_logger)

        # ハンドラが登録されていることを確認
        assert len(fake_handler.decorators) == 2

    def test_bind_routes_creates_default_line_adapter_if_not_provided(
        self, monkeypatch
    ):
        """bind_routes が line_adapter が未提供の場合デフォルトを生成すること"""
        fake_app = Mock()
        fake_app.route = Mock()

        fake_handler = FakeWebhookHandler()
        fake_logger = FakeLogger()

        # LINE 環境変数を設定
        monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "test-token")
        monkeypatch.setenv("LINE_CHANNEL_SECRET", "test-secret")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # line_adapter を提供しない
        bind_routes(fake_app, fake_handler, line_adapter=None, logger=fake_logger)

        # ハンドラが登録されていることを確認（内部でデフォルト adapter が生成される）
        assert len(fake_handler.decorators) == 2

    def test_bind_routes_creates_default_logger_if_not_provided(self, monkeypatch):
        """bind_routes が logger が未提供の場合デフォルトを生成すること"""
        fake_app = Mock()
        fake_app.route = Mock()

        fake_handler = FakeWebhookHandler()
        fake_line_adapter = FakeLineAdapter()

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # logger を提供しない
        bind_routes(fake_app, fake_handler, fake_line_adapter, logger=None)

        # ハンドラが登録されていることを確認
        assert len(fake_handler.decorators) == 2
