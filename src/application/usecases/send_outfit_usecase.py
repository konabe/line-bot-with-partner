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

    def execute(self, event, text: str) -> None:
        temp = self._parse_temperature(text or "")
        if temp is None:
            self._reply_with_text(
                event, "温度指定が見つかりませんでした。例: 20度の服装"
            )
            return

        now = datetime.datetime.now(ZoneInfo("Asia/Tokyo"))
        requirements = self._build_outfit_requirements(temp, now.month)

        image_url = self._generate_outfit_image(requirements)
        if not image_url:
            self._reply_with_text(
                event, "画像の生成に失敗しました。後でもう一度お試しください。"
            )
            return

        self._reply_with_image(event, image_url)

    def _parse_temperature(self, text: str) -> Optional[int]:
        m = re.search(r"(\d{1,2})\s*度の服装", text)
        if not m:
            return None
        try:
            return int(m.group(1))
        except ValueError:
            return None

    def _reply_with_text(self, event, message: str) -> None:
        reply = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text=message, quickReply=None, quoteToken=None)],
            notificationDisabled=False,
        )
        self._line_adapter.reply_message(reply)

    def _reply_with_image(self, event, image_url: str) -> None:
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

    def _build_outfit_requirements(self, temperature: int, month: int) -> str:
        return f"アラサーの日本人男性と日本人女性に適した、{month}月の雰囲気に合う摂氏{temperature}度の服装コーディネート。キレイ目のファッション。"

    def _generate_outfit_image(self, requirements: str) -> Optional[str]:
        try:
            image_prompt = self._openai_adapter.generate_image_prompt(requirements)
            return self._openai_adapter.generate_image(image_prompt)
        except Exception:
            return None
