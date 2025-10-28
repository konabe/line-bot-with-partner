import logging
from .usecases.send_janken_options_usecase import SendJankenOptionsUsecase
from typing import Protocol, Callable
from .usecases.send_weather_usecase import SendWeatherUsecase
from .usecases.send_meal_usecase import SendMealUsecase
from .usecases.send_chat_response_usecase import SendChatResponseUsecase
from ..infrastructure.line_model.zukan_button_template import (
    create_pokemon_zukan_button_template,
)
from linebot.v3.messaging import models

logger = logging.getLogger(__name__)


class DomainServices(Protocol):
    """Domain層サービスのインターフェース"""

    get_chatgpt_meal_suggestion: Callable[[], str]
    get_chatgpt_response: Callable[[str], str]
    # weather_adapter: object that provides get_weather_text(location: str) -> str
    weather_adapter: object


class MessageHandler:
    """LINEメッセージイベントを処理するハンドラークラス"""

    def __init__(self, safe_reply_message: Callable, domain_services: DomainServices):
        self.safe_reply_message = safe_reply_message
        self.domain_services = domain_services

    def handle_message(self, event) -> None:
        """LINE からのテキストメッセージイベントを処理します。"""
        text = event.message.text
        logger.debug(f"handle_message called. text: {text}")

        t = text.strip()
        if "天気" in text:
            return self._handle_weather(event, text)
        if t == "じゃんけん":
            return self._handle_janken(event)
        if t == "今日のご飯":
            return self._handle_meal(event)
        if t == "ポケモン":
            return self._handle_pokemon(event)
        if t.startswith("ぐんまちゃん、"):
            return self._handle_chatgpt(event, text)

    def _handle_weather(self, event, text: str) -> None:
        logger.info("天気リクエスト検出: usecase に委譲")
        SendWeatherUsecase(
            self.safe_reply_message, self.domain_services.weather_adapter
        ).execute(event, text)

    def _handle_janken(self, event) -> None:
        logger.info("じゃんけんテンプレートを送信 (usecase に委譲)")
        SendJankenOptionsUsecase(self.safe_reply_message).execute(event)

    def _handle_meal(self, event) -> None:
        logger.info("今日のご飯リクエストを受信: usecase に委譲")
        SendMealUsecase(
            self.safe_reply_message, self.domain_services.get_chatgpt_meal_suggestion
        ).execute(event)

    def _handle_pokemon(self, event) -> None:
        """ポケモンリクエストを処理します。図鑑情報を取得して TemplateMessage (Buttons) を送信します。"""
        logger.info("ポケモンリクエスト受信。図鑑風情報を返信")
        info = self._get_random_pokemon_zukan_info()
        if not info:
            from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

            reply_message_request = ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[
                    TextMessage(
                        text="ポケモン図鑑情報の取得に失敗しました。",
                        quickReply=None,
                        quoteToken=None,
                    )
                ],
                notificationDisabled=False,
            )
            self.safe_reply_message(reply_message_request)
            return

        try:
            candidate = create_pokemon_zukan_button_template(info)
            try:
                if hasattr(candidate, "dict") and candidate.__class__.__name__ in (
                    "TextMessage",
                    "TemplateMessage",
                ):
                    from linebot.v3.messaging.models import ReplyMessageRequest

                    reply_message_request = ReplyMessageRequest(
                        replyToken=event.reply_token,
                        messages=[candidate],
                        notificationDisabled=False,
                    )
                    self.safe_reply_message(reply_message_request)
                    return
            except Exception:
                # continue to dict handling below
                pass

            sdk_req = models.ReplyMessageRequest.parse_obj(
                {"replyToken": event.reply_token, "messages": [candidate]}
            )
            self.safe_reply_message(sdk_req)
            return
        except Exception as e:
            logger.error(f"ポケモンメッセージ送信エラー: {e}")
            from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

            reply_message_request = ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[
                    TextMessage(
                        text="ポケモン図鑑情報の送信に失敗しました。",
                        quickReply=None,
                        quoteToken=None,
                    )
                ],
                notificationDisabled=False,
            )
            self.safe_reply_message(reply_message_request)

    def _handle_chatgpt(self, event, text: str) -> None:
        logger.info("コマンド以外のメッセージを受信: usecase に委譲")
        SendChatResponseUsecase(
            self.safe_reply_message, self.domain_services.get_chatgpt_response
        ).execute(event, text)

    def _get_random_pokemon_zukan_info(self):
        """ランダムなポケモンの図鑑情報を取得します"""
        import random

        try:
            import requests

            # ランダムなポケモンを取得（1-1000の範囲）
            poke_id = random.randint(1, 1000)
            resp = requests.get(
                f"https://pokeapi.co/api/v2/pokemon/{poke_id}", timeout=10
            )
            resp.raise_for_status()
            data = resp.json()

            # 基本情報
            zukan_no = data["id"]
            name_en = data["name"]

            # 日本語名を取得
            name = name_en  # デフォルトは英語
            species_url = data.get("species", {}).get("url")
            if species_url:
                try:
                    species_resp = requests.get(species_url, timeout=10)
                    species_resp.raise_for_status()
                    species_data = species_resp.json()
                    for name_info in species_data.get("names", []):
                        if name_info.get("language", {}).get("name") == "ja":
                            name = name_info.get("name")
                            break
                except Exception:
                    pass  # 日本語名取得失敗時は英語名を使用

            # タイプ
            types = [t["type"]["name"] for t in data.get("types", [])]

            # 画像URL
            image_url = (
                data.get("sprites", {})
                .get("other", {})
                .get("official-artwork", {})
                .get("front_default")
            )

            # 進化情報（簡易版）
            evolution = "基本形"  # 簡易実装

            return {
                "zukan_no": zukan_no,
                "name": name,
                "types": types,
                "image_url": image_url,
                "evolution": evolution,
            }
        except Exception as e:
            logger.error(f"ポケモン情報取得エラー: {e}")
            return None
