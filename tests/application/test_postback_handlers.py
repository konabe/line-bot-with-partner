import pytest

class FakeJankenGame:
    behavior = None
    instantiated_count = 0

    def __init__(self):
        FakeJankenGame.instantiated_count += 1

    def play(self, user_hand):
        if FakeJankenGame.behavior is None:
            return {'user_hand': user_hand, 'bot_hand': '✌️', 'result': 'あなたの勝ち！'}
        return FakeJankenGame.behavior(user_hand)


def _make_event(data):
    class FakePostback:
        def __init__(self, data):
            self.data = data

    class FakeEvent:
        def __init__(self, data):
            self.postback = FakePostback(data)
            self.reply_token = 'dummy'
            class _Src:
                def __init__(self, uid: str = 'U111'):
                    self.user_id = uid
                    self.userId = uid

            self.source = _Src('U111')

    return FakeEvent(data)


def test_handle_postback_success(monkeypatch):
    """ポストバックでじゃんけんが正常に処理され、reply が送信されること"""
    from src.application import postback_handlers

    # configure shared fake to return deterministic result
    FakeJankenGame.behavior = lambda uh: {'user_hand': uh, 'bot_hand': '✌️', 'result': 'あなたの勝ち！'}
    FakeJankenGame.instantiated_count = 0

    monkeypatch.setattr(postback_handlers, 'JankenGame', FakeJankenGame)

    sent = []

    def fake_safe_reply(req):
        sent.append(req)

    event = _make_event('janken:✊')

    # construct handler with a simple fake logger and call instance method
    class _FakeLogger:
        def debug(self, msg): pass
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass
        def exception(self, msg): pass

    handler = postback_handlers.PostbackHandler(_FakeLogger(), fake_safe_reply, lambda uid: 'Alice')
    handler.handle_postback(event)

    assert len(sent) == 1
    req = sent[0]
    text = str(req.messages[0].text) if hasattr(req.messages[0], 'text') else str(req.messages[0])
    assert 'あなた (Alice): ✊' in text
    assert 'Bot: ✌️' in text
    assert '結果: あなたの勝ち！' in text


def test_handle_postback_invalid_hand(monkeypatch):
    """無効な手の場合、エラーメッセージが reply されること"""
    from src.application import postback_handlers

    def raise_invalid(user_hand):
        raise ValueError(f"無効な手です: {user_hand}")

    FakeJankenGame.behavior = raise_invalid
    FakeJankenGame.instantiated_count = 0

    monkeypatch.setattr(postback_handlers, 'JankenGame', FakeJankenGame)

    sent = []

    def fake_safe_reply(req):
        sent.append(req)

    event = _make_event('janken:invalid')

    class _FakeLogger:
        def debug(self, msg): pass
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass
        def exception(self, msg): pass

    handler = postback_handlers.PostbackHandler(_FakeLogger(), fake_safe_reply, lambda uid: 'Alice')
    handler.handle_postback(event)

    assert len(sent) == 1
    req = sent[0]
    text = str(req.messages[0].text) if hasattr(req.messages[0], 'text') else str(req.messages[0])
    assert 'あなた (Alice): invalid' in text
    assert 'エラー: 無効な手です: invalid' in text


def test_handle_postback_non_janken(monkeypatch):
    """janken: で始まらないデータでは何も送信されないこと"""
    from src.application import postback_handlers

    # Ensure fake is set but we can detect instantiation count
    FakeJankenGame.behavior = lambda uh: {}
    FakeJankenGame.instantiated_count = 0

    monkeypatch.setattr(postback_handlers, 'JankenGame', FakeJankenGame)

    sent = []

    def fake_safe_reply(req):
        sent.append(req)

    event = _make_event('other:foo')

    class _FakeLogger:
        def debug(self, msg): pass
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass
        def exception(self, msg): pass

    handler = postback_handlers.PostbackHandler(_FakeLogger(), fake_safe_reply, lambda uid: 'Alice')
    handler.handle_postback(event)

    # Should not have called safe_reply_message nor instantiated JankenGame
    assert sent == []
    assert FakeJankenGame.instantiated_count == 0
