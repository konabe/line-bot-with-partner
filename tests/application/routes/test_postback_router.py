"""PostbackRouter の単体テスト"""

from typing import cast

import pytest

from src.application.routes.postback_router import PostbackRouter
from src.application.types import PostbackEventLike


class FakeLineAdapter:
    """テスト用 LINE アダプタ"""

    def __init__(self):
        self.reply_message_calls = []
        self.push_message_calls = []

    def reply_message(self, req):
        self.reply_message_calls.append(req)

    def push_message(self, req):
        self.push_message_calls.append(req)
        return True

    def get_display_name_from_line_profile(self, user_id: str) -> str:
        return "TestUser"


class FakeOpenAIAdapter:
    """テスト用 OpenAI アダプタ"""

    def __init__(self):
        self.track_score_calls = []

    def get_chatgpt_response(self, user_message: str) -> str:
        return "AI response"

    def generate_image(self, prompt: str) -> str:
        return "https://example.com/image.png"

    def generate_image_prompt(self, requirements: str) -> str:
        return "A detailed image prompt"

    def get_chatgpt_meal_suggestion(self, return_request_id: bool = False):
        if return_request_id:
            return "Meal suggestion", 12345
        return "Meal suggestion"

    def track_score(
        self, request_id: int, score: int, score_name: str = "user_feedback"
    ) -> bool:
        self.track_score_calls.append((request_id, score, score_name))
        return True


class FakeJankenService:
    """テスト用じゃんけんサービス"""

    def __init__(self):
        self.play_and_make_reply_calls = []

    def play_and_make_reply(self, user_hand_input: str, user_label: str) -> str:
        self.play_and_make_reply_calls.append((user_hand_input, user_label))
        return f"{user_label}: {user_hand_input}\nBot: ✌️\n結果: あなたの勝ち！"


class FakeLogger:
    """テスト用ロガー"""

    def __init__(self):
        self.debug_logs = []
        self.info_logs = []
        self.warning_logs = []
        self.error_logs = []
        self.exception_logs = []

    def debug(self, msg, *args):
        self.debug_logs.append(msg)

    def info(self, msg, *args):
        self.info_logs.append(msg)

    def warning(self, msg, *args):
        self.warning_logs.append(msg)

    def error(self, msg, *args):
        self.error_logs.append(msg)

    def exception(self, msg, *args):
        self.exception_logs.append(msg)


def _make_postback_event(data: str | None, user_id: str = "U123"):
    """PostbackEvent 風のオブジェクトを作成"""

    class FakePostback:
        def __init__(self, data: str | None):
            self.data = data

    class FakeSource:
        def __init__(self, user_id: str):
            self.user_id = user_id
            self.type = "user"

    class FakeEvent:
        def __init__(self, data: str | None, user_id: str):
            self.postback = FakePostback(data)
            self.reply_token = "dummy_token"
            self.source = FakeSource(user_id)
            self.type = "postback"

    return FakeEvent(data, user_id)


class TestPostbackRouterEventHandling:
    """route_postback の event 引数処理テスト"""

    def test_route_postback_with_none_event_logs_error_and_returns(self):
        """event=None の場合、エラーログを出して早期リターンすること"""
        line_adapter = FakeLineAdapter()
        openai_adapter = FakeOpenAIAdapter()
        janken_service = FakeJankenService()
        logger = FakeLogger()

        router = PostbackRouter(
            line_adapter, openai_adapter, janken_service, logger=logger
        )

        # event=None で呼び出し
        router.route_postback(event=None)

        # エラーログが出ていることを確認
        assert any(
            "route_postback called" in log and "event" in log
            for log in logger.error_logs
        )
        # アダプタが呼ばれていないことを確認
        assert len(line_adapter.reply_message_calls) == 0

    def test_route_postback_with_extra_argument(self):
        """extra 引数が渡された場合も処理できること"""
        line_adapter = FakeLineAdapter()
        janken_service = FakeJankenService()
        logger = FakeLogger()

        router = PostbackRouter(
            line_adapter, FakeOpenAIAdapter(), janken_service, logger=logger
        )

        event = _make_postback_event("janken:✊")

        # extra に文字列を渡す
        router.route_postback(event, extra="some_extra_data")

        # じゃんけんが呼ばれていることを確認
        assert len(line_adapter.reply_message_calls) == 1


class TestPostbackRouterJankenHandling:
    """じゃんけんポストバック処理のテスト"""

    def test_route_janken_postback_rock(self):
        """janken:✊ のポストバックがじゃんけん usecase に委譲されること"""
        line_adapter = FakeLineAdapter()
        janken_service = FakeJankenService()
        logger = FakeLogger()

        router = PostbackRouter(
            line_adapter, FakeOpenAIAdapter(), janken_service, logger=logger
        )

        event = _make_postback_event("janken:✊")
        router.route_postback(cast(PostbackEventLike, event))

        # じゃんけんサービスが呼ばれていることを確認
        assert len(janken_service.play_and_make_reply_calls) == 1
        assert janken_service.play_and_make_reply_calls[0][0] == "✊"

    def test_route_janken_postback_scissors(self):
        """janken:✌️ のポストバックがじゃんけん usecase に委譲されること"""
        line_adapter = FakeLineAdapter()
        janken_service = FakeJankenService()
        logger = FakeLogger()

        router = PostbackRouter(
            line_adapter, FakeOpenAIAdapter(), janken_service, logger=logger
        )

        event = _make_postback_event("janken:✌️")
        router.route_postback(cast(PostbackEventLike, event))

        # じゃんけんサービスが呼ばれていることを確認
        assert len(janken_service.play_and_make_reply_calls) == 1
        assert janken_service.play_and_make_reply_calls[0][0] == "✌️"

    def test_route_janken_postback_paper(self):
        """janken:✋ のポストバックがじゃんけん usecase に委譲されること"""
        line_adapter = FakeLineAdapter()
        janken_service = FakeJankenService()
        logger = FakeLogger()

        router = PostbackRouter(
            line_adapter, FakeOpenAIAdapter(), janken_service, logger=logger
        )

        event = _make_postback_event("janken:✋")
        router.route_postback(cast(PostbackEventLike, event))

        # じゃんけんサービスが呼ばれていることを確認
        assert len(janken_service.play_and_make_reply_calls) == 1
        assert janken_service.play_and_make_reply_calls[0][0] == "✋"


class TestPostbackRouterNoneData:
    """postback.data が None の場合のテスト"""

    def test_route_postback_with_none_data_logs_and_returns(self):
        """postback.data が None の場合、ログを出して早期リターンすること"""
        line_adapter = FakeLineAdapter()
        janken_service = FakeJankenService()
        logger = FakeLogger()

        router = PostbackRouter(
            line_adapter, FakeOpenAIAdapter(), janken_service, logger=logger
        )

        event = _make_postback_event(None)
        router.route_postback(cast(PostbackEventLike, event))

        # デバッグログに None を記録していることを確認
        assert any("postback.data is None" in log for log in logger.debug_logs)
        # アダプタが呼ばれていないことを確認
        assert len(line_adapter.reply_message_calls) == 0


class TestPostbackRouterUnmatchedData:
    """janken: で始まらない postback.data のテスト"""

    def test_route_postback_with_unmatched_data_does_not_call_usecase(self):
        """janken: で始まらない data は何も呼ばれないこと"""
        line_adapter = FakeLineAdapter()
        janken_service = FakeJankenService()
        logger = FakeLogger()

        router = PostbackRouter(
            line_adapter, FakeOpenAIAdapter(), janken_service, logger=logger
        )

        event = _make_postback_event("other:action")
        router.route_postback(cast(PostbackEventLike, event))

        # じゃんけんサービスが呼ばれていないことを確認
        assert len(janken_service.play_and_make_reply_calls) == 0
        assert len(line_adapter.reply_message_calls) == 0


class TestPostbackRouterMealFeedbackHandling:
    """料理評価ポストバック処理のテスト"""

    def test_route_meal_feedback_postback_success(self):
        """meal_feedback: のポストバックが正常に処理されること"""

        class FakeOpenAIAdapter:
            def __init__(self):
                self.track_score_calls = []

            def track_score(self, request_id: int, score: int, score_name: str = "user_feedback") -> bool:
                self.track_score_calls.append(
                    {"request_id": request_id, "score": score, "score_name": score_name}
                )
                return True

        line_adapter = FakeLineAdapter()
        openai_adapter = FakeOpenAIAdapter()
        logger = FakeLogger()

        router = PostbackRouter(
            line_adapter, openai_adapter, FakeJankenService(), logger=logger
        )

        event = _make_postback_event("meal_feedback:12345:100")
        router.route_postback(cast(PostbackEventLike, event))

        # OpenAI adapter が呼ばれていることを確認
        assert len(openai_adapter.track_score_calls) == 1
        assert openai_adapter.track_score_calls[0]["request_id"] == 12345
        assert openai_adapter.track_score_calls[0]["score"] == 100

        # 感謝メッセージが送信されていることを確認
        assert len(line_adapter.reply_message_calls) == 1
