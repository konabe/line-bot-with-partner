import datetime
import re
from typing import Optional
from zoneinfo import ZoneInfo

from linebot.v3.messaging.models import ImageMessage, ReplyMessageRequest, TextMessage

from .protocols import LineAdapterProtocol, OpenAIAdapterProtocol


class SendOutfitUsecase:
    def __init__(
        self, line_adapter: LineAdapterProtocol, openai_adapter: OpenAIAdapterProtocol
    ):
        self._line_adapter = line_adapter
        self._openai_adapter = openai_adapter

    def _parse_temperature(self, text: str) -> Optional[int]:
        m = re.search(r"(\d{1,2})\s*度の服装", text)
        if not m:
            return None
        try:
            return int(m.group(1))
        except Exception:
            return None

    def execute(self, event, text: str) -> None:
        temp = self._parse_temperature(text or "")
        if temp is None:
            reply = ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[
                    TextMessage(
                        text="温度指定が見つかりませんでした。例: 20度の服装",
                        quickReply=None,
                        quoteToken=None,
                    )
                ],
                notificationDisabled=False,
            )
            self._line_adapter.reply_message(reply)
            return

        now = datetime.datetime.now(ZoneInfo("Asia/Tokyo"))
        month = now.month
        requirements = (
            f"アラサーの日本人男性と日本人女性に適した、{month}月の雰囲気に合う摂氏{temp}度の服装コーディネート。キレイ目のファッション。"
        )

        try:
            # GPTにDALL-E 3用のプロンプトを生成させる
            image_prompt = self._openai_adapter.generate_image_prompt(requirements)
            # 生成されたプロンプトで画像を作成
            image_url = self._openai_adapter.generate_image(image_prompt)
        except Exception:
            image_url = None

        if not image_url:
            reply = ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[
                    TextMessage(
                        text="画像の生成に失敗しました。後でもう一度お試しください。",
                        quickReply=None,
                        quoteToken=None,
                    )
                ],
                notificationDisabled=False,
            )
            self._line_adapter.reply_message(reply)
            return

        reply = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[
                ImageMessage(
                    originalContentUrl=image_url,
                    previewImageUrl=image_url,
                    quickReply=None,
                )
            ],
            notificationDisabled=False,
        )

        self._line_adapter.reply_message(reply)
