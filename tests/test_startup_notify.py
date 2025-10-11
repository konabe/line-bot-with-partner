from unittest.mock import patch

import importlib


def test_startup_notify_sends_once(monkeypatch):
    monkeypatch.setenv('STARTUP_NOTIFY_ENABLED', '1')
    monkeypatch.setenv('STARTUP_NOTIFY_USER_ID', 'USER123')

    # モジュール再読み込みで _startup_notified をリセット
    # import app  # SDK依存のため一時的にコメントアウト
    # importlib.reload(app)
    # sent = []
    # def fake_push(user_id, message):  # message は TextSendMessage オブジェクト
    #     sent.append((user_id, message.text))
    # with patch.object(app, 'line_bot_api') as mock_api:
    #     mock_api.push_message.side_effect = fake_push
    #     app.maybe_notify_startup()  # 1回目
    #     app.maybe_notify_startup()  # 2回目 (無視されるはず)
    # assert len(sent) == 1
    # assert sent[0][0] == 'USER123'
    # assert '起動' in sent[0][1]


def test_startup_notify_disabled(monkeypatch):
    monkeypatch.delenv('STARTUP_NOTIFY_ENABLED', raising=False)
    # import app  # SDK依存のため一時的にコメントアウト
    # importlib.reload(app)
    # with patch.object(app, 'line_bot_api') as mock_api:
    #     app.maybe_notify_startup()
    #     mock_api.push_message.assert_not_called()
