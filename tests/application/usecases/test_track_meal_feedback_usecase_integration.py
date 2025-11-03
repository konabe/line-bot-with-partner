from unittest.mock import MagicMock

from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

from src.application.usecases.track_meal_feedback_usecase import (
    TrackMealFeedbackUsecase,
)
from tests.support.mock_adapter import MockMessagingAdapter


class FakeEvent:
    def __init__(self):
        self.reply_token = "test_reply_token_123"


def test_execute_with_successful_score_tracking():
    """スコア送信が成功した場合の結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_openai_adapter = MagicMock()
    mock_openai_adapter.track_score.return_value = True

    usecase = TrackMealFeedbackUsecase(mock_line_adapter, mock_openai_adapter)
    event = FakeEvent()

    result = usecase.execute(event, pl_request_id=12345, score=100)

    assert result is True
    mock_openai_adapter.track_score.assert_called_once_with(
        request_id=12345, score=100, score_name="user_feedback"
    )

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    assert isinstance(reply, ReplyMessageRequest)
    assert reply.reply_token == "test_reply_token_123"
    assert len(reply.messages) == 1
    assert isinstance(reply.messages[0], TextMessage)
    assert "評価ありがとう" in reply.messages[0].text


def test_execute_with_failed_score_tracking():
    """スコア送信が失敗した場合でも感謝メッセージが送信される結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_openai_adapter = MagicMock()
    mock_openai_adapter.track_score.return_value = False

    usecase = TrackMealFeedbackUsecase(mock_line_adapter, mock_openai_adapter)
    event = FakeEvent()

    result = usecase.execute(event, pl_request_id=12345, score=50)

    assert result is False
    mock_openai_adapter.track_score.assert_called_once_with(
        request_id=12345, score=50, score_name="user_feedback"
    )

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 1
    reply = replies[0]
    assert isinstance(reply.messages[0], TextMessage)
    assert "評価ありがとう" in reply.messages[0].text


def test_execute_with_good_score():
    """良い評価(100点)の結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_openai_adapter = MagicMock()
    mock_openai_adapter.track_score.return_value = True

    usecase = TrackMealFeedbackUsecase(mock_line_adapter, mock_openai_adapter)
    event = FakeEvent()

    result = usecase.execute(event, pl_request_id=99999, score=100)

    assert result is True
    mock_openai_adapter.track_score.assert_called_once_with(
        request_id=99999, score=100, score_name="user_feedback"
    )


def test_execute_with_normal_score():
    """普通の評価(50点)の結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_openai_adapter = MagicMock()
    mock_openai_adapter.track_score.return_value = True

    usecase = TrackMealFeedbackUsecase(mock_line_adapter, mock_openai_adapter)
    event = FakeEvent()

    result = usecase.execute(event, pl_request_id=88888, score=50)

    assert result is True
    mock_openai_adapter.track_score.assert_called_once_with(
        request_id=88888, score=50, score_name="user_feedback"
    )


def test_execute_with_bad_score():
    """悪い評価(0点)の結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_openai_adapter = MagicMock()
    mock_openai_adapter.track_score.return_value = True

    usecase = TrackMealFeedbackUsecase(mock_line_adapter, mock_openai_adapter)
    event = FakeEvent()

    result = usecase.execute(event, pl_request_id=77777, score=0)

    assert result is True
    mock_openai_adapter.track_score.assert_called_once_with(
        request_id=77777, score=0, score_name="user_feedback"
    )


def test_execute_with_track_score_exception():
    """track_scoreで例外が発生した場合は例外が発生する結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_openai_adapter = MagicMock()
    mock_openai_adapter.track_score.side_effect = RuntimeError("PromptLayer API Error")

    usecase = TrackMealFeedbackUsecase(mock_line_adapter, mock_openai_adapter)
    event = FakeEvent()

    exception_raised = False
    try:
        usecase.execute(event, pl_request_id=12345, score=100)
    except RuntimeError:
        exception_raised = True

    assert exception_raised


def test_execute_multiple_feedbacks():
    """複数のフィードバックが順次処理される結合テスト"""
    mock_line_adapter = MockMessagingAdapter()
    mock_openai_adapter = MagicMock()
    mock_openai_adapter.track_score.return_value = True

    usecase = TrackMealFeedbackUsecase(mock_line_adapter, mock_openai_adapter)

    test_cases = [
        (12345, 100),
        (23456, 50),
        (34567, 0),
    ]

    for idx, (request_id, score) in enumerate(test_cases):
        event = FakeEvent()
        event.reply_token = f"token_{idx}"
        result = usecase.execute(event, pl_request_id=request_id, score=score)
        assert result is True

    assert mock_openai_adapter.track_score.call_count == 3

    replies = mock_line_adapter.get_replies()
    assert len(replies) == 3

    for reply in replies:
        assert isinstance(reply, ReplyMessageRequest)
        assert len(reply.messages) == 1
        assert isinstance(reply.messages[0], TextMessage)
