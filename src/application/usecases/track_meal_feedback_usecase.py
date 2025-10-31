from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

from .protocols import LineAdapterProtocol, OpenAIAdapterProtocol


class TrackMealFeedbackUsecase:
    def __init__(
        self,
        line_adapter: LineAdapterProtocol,
        openai_adapter: OpenAIAdapterProtocol,
    ):
        self._line_adapter = line_adapter
        self._openai_adapter = openai_adapter

    def execute(self, event, pl_request_id: int, score: int) -> bool:
        """料理提案の評価をPromptLayerに送信する

        Args:
            event: LINEイベント
            pl_request_id: PromptLayerリクエストID
            score: 評価スコア (0-100)

        Returns:
            スコア送信の成功/失敗
        """
        # スコアをPromptLayerに送信
        success = self._openai_adapter.track_score(
            request_id=pl_request_id, score=score, score_name="user_feedback"
        )

        # ユーザーに感謝のメッセージを返信
        feedback_msg = "評価ありがとうございます！😊"
        reply_message_request = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text=feedback_msg, quickReply=None, quoteToken=None)],
            notificationDisabled=False,
        )
        self._line_adapter.reply_message(reply_message_request)

        return success
