from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

from src.application.usecases.track_meal_feedback_usecase import (
    TrackMealFeedbackUsecase,
)


class FakeEvent:
    def __init__(self):
        self.reply_token = "dummy_token"


class FakeLineAdapter:
    def __init__(self):
        self.reply_message_calls = []

    def reply_message(self, req: ReplyMessageRequest):
        self.reply_message_calls.append(req)

    def push_message(self, req):
        pass

    def get_display_name_from_line_profile(self, user_id):
        return None


class FakeOpenAIAdapter:
    def __init__(self, track_score_result: bool = True):
        self.track_score_calls = []
        self.track_score_result = track_score_result

    def track_score(
        self, request_id: int, score: int, score_name: str = "user_feedback"
    ) -> bool:
        self.track_score_calls.append(
            {"request_id": request_id, "score": score, "score_name": score_name}
        )
        return self.track_score_result

    def get_chatgpt_response(self, user_message: str) -> str:
        return ""

    def generate_image(self, prompt: str) -> str:
        return ""

    def generate_image_prompt(self, requirements: str) -> str:
        return ""

    def get_chatgpt_meal_suggestion(self, return_request_id: bool = False):
        return ""


def test_execute_success():
    """フィードバックが正常に送信できること"""
    line_adapter = FakeLineAdapter()
    openai_adapter = FakeOpenAIAdapter(track_score_result=True)

    usecase = TrackMealFeedbackUsecase(line_adapter, openai_adapter)
    event = FakeEvent()

    result = usecase.execute(event, postback_data="meal_feedback:12345:100")

    # スコアが送信されていることを確認
    assert len(openai_adapter.track_score_calls) == 1
    assert openai_adapter.track_score_calls[0]["request_id"] == 12345
    assert openai_adapter.track_score_calls[0]["score"] == 100
    assert openai_adapter.track_score_calls[0]["score_name"] == "user_feedback"

    # 感謝メッセージが送信されていることを確認
    assert len(line_adapter.reply_message_calls) == 1
    req = line_adapter.reply_message_calls[0]
    assert isinstance(req, ReplyMessageRequest)
    assert req.reply_token == event.reply_token
    assert len(req.messages) == 1
    assert isinstance(req.messages[0], TextMessage)
    assert "評価ありがとうございます" in req.messages[0].text

    # 成功を返すこと
    assert result is True


def test_execute_track_score_failure():
    """スコア送信が失敗しても感謝メッセージは送信されること"""
    line_adapter = FakeLineAdapter()
    openai_adapter = FakeOpenAIAdapter(track_score_result=False)

    usecase = TrackMealFeedbackUsecase(line_adapter, openai_adapter)
    event = FakeEvent()

    result = usecase.execute(event, postback_data="meal_feedback:12345:50")

    # スコア送信が試行されていることを確認
    assert len(openai_adapter.track_score_calls) == 1

    # 感謝メッセージは送信されていることを確認
    assert len(line_adapter.reply_message_calls) == 1

    # 失敗を返すこと
    assert result is False


def test_execute_with_different_scores():
    """異なるスコアで正常に動作すること"""
    line_adapter = FakeLineAdapter()
    openai_adapter = FakeOpenAIAdapter()

    usecase = TrackMealFeedbackUsecase(line_adapter, openai_adapter)
    event = FakeEvent()

    # スコア0（悪い）
    usecase.execute(event, postback_data="meal_feedback:11111:0")
    assert openai_adapter.track_score_calls[-1]["score"] == 0

    # スコア50（普通）
    usecase.execute(event, postback_data="meal_feedback:22222:50")
    assert openai_adapter.track_score_calls[-1]["score"] == 50

    # スコア100（良い）
    usecase.execute(event, postback_data="meal_feedback:33333:100")
    assert openai_adapter.track_score_calls[-1]["score"] == 100

    assert len(openai_adapter.track_score_calls) == 3


def test_execute_with_invalid_format():
    """無効なデータフォーマットの場合はFalseを返すこと"""
    line_adapter = FakeLineAdapter()
    openai_adapter = FakeOpenAIAdapter()

    usecase = TrackMealFeedbackUsecase(line_adapter, openai_adapter)
    event = FakeEvent()

    # コロン区切りが不足
    result = usecase.execute(event, postback_data="meal_feedback:12345")
    assert result is False
    assert len(openai_adapter.track_score_calls) == 0
    assert len(line_adapter.reply_message_calls) == 0

    # コロン区切りが多すぎる
    result = usecase.execute(event, postback_data="meal_feedback:12345:100:extra")
    assert result is False
    assert len(openai_adapter.track_score_calls) == 0
    assert len(line_adapter.reply_message_calls) == 0


def test_execute_with_invalid_values():
    """無効な数値の場合はFalseを返すこと"""
    line_adapter = FakeLineAdapter()
    openai_adapter = FakeOpenAIAdapter()

    usecase = TrackMealFeedbackUsecase(line_adapter, openai_adapter)
    event = FakeEvent()

    # request_idが数値でない
    result = usecase.execute(event, postback_data="meal_feedback:abc:100")
    assert result is False
    assert len(openai_adapter.track_score_calls) == 0
    assert len(line_adapter.reply_message_calls) == 0

    # scoreが数値でない
    result = usecase.execute(event, postback_data="meal_feedback:12345:xyz")
    assert result is False
    assert len(openai_adapter.track_score_calls) == 0
    assert len(line_adapter.reply_message_calls) == 0
