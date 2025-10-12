from src.application.startup_notify import notify_startup_if_configured


class LoggerStub:
    def __init__(self):
        self.debug_messages = []
        self.info_messages = []
        self.error_messages = []

    def debug(self, message):
        self.debug_messages.append(message)

    def info(self, message):
        self.info_messages.append(message)

    def error(self, message):
        self.error_messages.append(message)


def test_notify_startup_sends_message(monkeypatch):
    monkeypatch.setenv('ADMIN_USER_ID', 'USER123')
    monkeypatch.delenv('ADMIN_STARTUP_MESSAGE', raising=False)
    sent = []

    def fake_safe_push(request):
        sent.append(request)

    logger = LoggerStub()

    result = notify_startup_if_configured(fake_safe_push, logger)

    assert result is True
    assert sent
    push_req = sent[0]
    assert push_req.to == 'USER123'
    assert push_req.messages[0].text == 'サーバーが起動しました。'
    assert any('startup notification sent' in msg for msg in logger.info_messages)


def test_notify_startup_skips_when_admin_missing(monkeypatch):
    monkeypatch.delenv('ADMIN_USER_ID', raising=False)
    sent = []

    def fake_safe_push(request):
        sent.append(request)

    logger = LoggerStub()

    result = notify_startup_if_configured(fake_safe_push, logger)

    assert result is False
    assert sent == []
    assert any('skipping startup notification' in msg for msg in logger.debug_messages)


def test_notify_startup_logs_error_on_failure(monkeypatch):
    monkeypatch.setenv('ADMIN_USER_ID', 'USER123')

    def failing_safe_push(request):
        raise RuntimeError('push failed')

    logger = LoggerStub()

    result = notify_startup_if_configured(failing_safe_push, logger)

    assert result is False
    assert any('failed to send startup notification' in msg for msg in logger.error_messages)
