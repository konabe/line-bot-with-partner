from linebot.v3.messaging.models import (
    ButtonsTemplate,
    PostbackAction,
    ReplyMessageRequest,
    TemplateMessage,
    TextMessage,
)

from .protocols import LineAdapterProtocol, OpenAIAdapterProtocol


class SendMealUsecase:
    def __init__(
        self,
        line_adapter: LineAdapterProtocol,
        openai_adapter: OpenAIAdapterProtocol,
    ):
        self._line_adapter = line_adapter
        self._openai_adapter = openai_adapter

    def execute(self, event) -> None:
        try:
            result = self._openai_adapter.get_chatgpt_meal_suggestion(
                return_request_id=True
            )
            if isinstance(result, tuple):
                suggestion, pl_request_id = result
            else:
                suggestion = result
                pl_request_id = None
        except Exception:
            suggestion = None
            pl_request_id = None

        if not suggestion:
            msg = "申し訳ないです。おすすめを取得できませんでした。" " 管理者に OPENAI_API_KEY の設定を確認てもらってください。"
            reply_message_request = ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[TextMessage(text=msg, quickReply=None, quoteToken=None)],
                notificationDisabled=False,
            )
        else:
            messages: list = [
                TextMessage(text=suggestion, quickReply=None, quoteToken=None)
            ]

            # PromptLayerリクエストIDがある場合は評価ボタンを追加
            if pl_request_id is not None:
                feedback_template = TemplateMessage(
                    altText="料理提案の評価をお願いします",
                    template=ButtonsTemplate(
                        title="評価",
                        text="この提案はいかがでしたか？",
                        actions=[
                            PostbackAction(
                                label="😊 良い",
                                data=f"meal_feedback:{pl_request_id}:100",
                                displayText=None,
                                inputOption=None,
                                fillInText=None,
                            ),
                            PostbackAction(
                                label="😐 普通",
                                data=f"meal_feedback:{pl_request_id}:50",
                                displayText=None,
                                inputOption=None,
                                fillInText=None,
                            ),
                            PostbackAction(
                                label="😞 悪い",
                                data=f"meal_feedback:{pl_request_id}:0",
                                displayText=None,
                                inputOption=None,
                                fillInText=None,
                            ),
                        ],
                        thumbnailImageUrl=None,
                        imageAspectRatio=None,
                        imageSize=None,
                        imageBackgroundColor=None,
                        defaultAction=None,
                    ),
                    quickReply=None,
                )
                messages.append(feedback_template)

            reply_message_request = ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=messages,
                notificationDisabled=False,
            )

        self._line_adapter.reply_message(reply_message_request)
