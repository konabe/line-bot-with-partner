from typing import Protocol

from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage


class SendChatResponseUsecase:
    """汎用的な ChatGPT 応答ユースケース。

    コンストラクタで safe_reply_message と chatgpt_callable を注入する。
    chatgpt_callable は (user_message: str) -> str を返す callable を想定します。
    """

    class LineAdapterProtocol(Protocol):
        def reply_message(self, req) -> None:
            ...

    class OpenAIAdapterProtocol(Protocol):
        def get_chatgpt_response(self, user_message: str) -> str:
            ...

    def __init__(
        self,
        line_adapter: LineAdapterProtocol,
        openai_adapter: OpenAIAdapterProtocol,
    ):
        """コンストラクタでアダプタのインスタンスを注入します。

        Args:
            line_adapter: `LineMessagingAdapter` のインスタンス（reply_message を持つこと）
            openai_adapter: `OpenAIAdapter` のインスタンス（get_chatgpt_response を持つこと）
        """
        self._line_adapter = line_adapter
        self._openai_adapter = openai_adapter

    def execute(self, event, user_message: str) -> None:
        """user_message に対してチャット応答を取得し、ReplyMessageRequest を送信する。"""
        try:
            response = None
            try:
                response = self._openai_adapter.get_chatgpt_response(user_message)
            except Exception:
                # OpenAI 側で何らかのエラーが発生した場合は None 扱いにしてユーザーに案内する
                response = None

            if not response:
                msg = "申し訳ないです。応答を生成できませんでした。" " 管理者に OPENAI_API_KEY の設定を確認してもらってください。"
                reply_message_request = ReplyMessageRequest(
                    replyToken=event.reply_token,
                    messages=[TextMessage(text=msg, quickReply=None, quoteToken=None)],
                    notificationDisabled=False,
                )
            else:
                reply_message_request = ReplyMessageRequest(
                    replyToken=event.reply_token,
                    messages=[
                        TextMessage(text=response, quickReply=None, quoteToken=None)
                    ],
                    notificationDisabled=False,
                )

            # Line adapter に送信を委譲する（safe wrapper は adapter 側で実装される想定）
            self._line_adapter.reply_message(reply_message_request)
        except Exception:
            # もし reply に失敗した場合はログ等は adapter 側で行われる想定なので
            # ここでは例外を吸収して処理を終える。
            return
