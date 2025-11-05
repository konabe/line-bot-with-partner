from typing import Optional
from unittest.mock import MagicMock, Mock

from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

from src.application.usecases.start_janken_game_usecase import StartJankenGameUsecase
from src.domain.services.janken_game_master_service import JankenGameMasterService
from tests.support.mock_adapter import MockMessagingAdapter


def _make_fake_event(hand: str, user_id: str = "U123456"):
    event = Mock()
    event.reply_token = "test_reply_token_123"
    event.postback = Mock()
    event.postback.data = f"janken:{hand}"
    event.source = Mock()
    event.source.user_id = user_id
    return event


def test_execute_with_valid_hand_guu():
    """グーを選択した場合の結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_line_adapter.get_display_name_from_line_profile = MagicMock(
        return_value="テストユーザー"
    )
    janken_service = JankenGameMasterService()

    usecase = StartJankenGameUsecase(mock_line_adapter, janken_service)
    event = _make_fake_event("✊")

    usecase.execute(event)  # type: ignore

    mock_line_adapter.get_display_name_from_line_profile.assert_called_once_with(
        "U123456"
    )

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    assert isinstance(reply, ReplyMessageRequest)
    assert reply.reply_token == "test_reply_token_123"
    assert len(reply.messages) == 1
    assert isinstance(reply.messages[0], TextMessage)

    result_text = reply.messages[0].text
    assert "あなた (テストユーザー): ✊" in result_text
    assert "Bot: " in result_text
    assert any(x in result_text for x in ["勝ち", "負け", "あいこ"])


def test_execute_with_valid_hand_choki():
    """チョキを選択した場合の結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_line_adapter.get_display_name_from_line_profile = MagicMock(
        return_value="テストユーザー"
    )
    janken_service = JankenGameMasterService()

    usecase = StartJankenGameUsecase(mock_line_adapter, janken_service)
    event = _make_fake_event("✌️")

    usecase.execute(event)  # type: ignore

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    result_text = reply.messages[0].text
    assert "あなた (テストユーザー): ✌️" in result_text


def test_execute_with_valid_hand_paa():
    """パーを選択した場合の結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_line_adapter.get_display_name_from_line_profile = MagicMock(
        return_value="テストユーザー"
    )
    janken_service = JankenGameMasterService()

    usecase = StartJankenGameUsecase(mock_line_adapter, janken_service)
    event = _make_fake_event("✋")

    usecase.execute(event)  # type: ignore

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    result_text = reply.messages[0].text
    assert "あなた (テストユーザー): ✋" in result_text


def test_execute_without_display_name():
    """表示名が取得できない場合でも正常に動作する結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_line_adapter.get_display_name_from_line_profile = MagicMock(return_value=None)
    janken_service = JankenGameMasterService()

    usecase = StartJankenGameUsecase(mock_line_adapter, janken_service)
    event = _make_fake_event("✊")

    usecase.execute(event)  # type: ignore

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    result_text = reply.messages[0].text
    assert "あなた: ✊" in result_text


def test_execute_with_profile_fetch_exception():
    """プロフィール取得時に例外が発生しても正常に動作する結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_line_adapter.get_display_name_from_line_profile = MagicMock(
        side_effect=RuntimeError("Profile API Error")
    )
    janken_service = JankenGameMasterService()

    usecase = StartJankenGameUsecase(mock_line_adapter, janken_service)
    event = _make_fake_event("✊")

    usecase.execute(event)  # type: ignore

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    result_text = reply.messages[0].text
    assert "あなた: ✊" in result_text


def test_execute_multiple_games():
    """複数回じゃんけんを実行しても正常に動作する結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_line_adapter.get_display_name_from_line_profile = MagicMock(
        return_value="テストユーザー"
    )
    janken_service = JankenGameMasterService()

    usecase = StartJankenGameUsecase(mock_line_adapter, janken_service)

    for hand in ["✊", "✌️", "✋"]:
        event = _make_fake_event(hand)
        usecase.execute(event)  # type: ignore

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 3

    for reply in replies:
        assert isinstance(reply, ReplyMessageRequest)
        assert len(reply.messages) == 1
        assert isinstance(reply.messages[0], TextMessage)
