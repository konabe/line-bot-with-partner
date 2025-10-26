import logging
from .usecases.send_janken_options_usecase import SendJankenOptionsUsecase
from typing import Protocol, Callable
from src.infrastructure.line_model import create_pokemon_zukan_flex_dict
from .usecases.send_weather_usecase import SendWeatherUsecase

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
        """
        MessageHandlerの初期化

        Args:
            safe_reply_message: 安全なメッセージ送信関数
            domain_services: ドメインサービス（省略時はデフォルトを使用）
        """
        self.safe_reply_message = safe_reply_message
        self.domain_services = domain_services

    def handle_message(self, event) -> None:
        """LINE からのテキストメッセージイベントを処理します。"""
        text = event.message.text
        logger.debug(f"handle_message called. text: {text}")
        try:
            user_id = getattr(event.source, 'user_id', None) or getattr(event.source, 'userId', None)
        except Exception:
            user_id = None

        t = text.strip()
        if '天気' in text:
            return self._handle_weather(event, text)
        if t == 'じゃんけん':
            return self._handle_janken(event)
        if t == '今日のご飯':
            return self._handle_meal(event)
        if t == 'ポケモン':
            return self._handle_pokemon(event)
        return self._handle_chatgpt(event, text)


    def _handle_weather(self, event, text: str) -> None:
        logger.info("天気リクエスト検出: usecase に委譲")
    SendWeatherUsecase(self.safe_reply_message, self.domain_services.weather_adapter).execute(event, text)

    def _handle_janken(self, event) -> None:
        logger.info("じゃんけんテンプレートを送信 (usecase に委譲)")
        SendJankenOptionsUsecase(self.safe_reply_message).execute(event)

    def _handle_meal(self, event) -> None:
        """今日のご飯リクエストを処理します"""
        logger.info("今日のご飯リクエストを受信: ChatGPT に問い合わせます")
        try:
            suggestion = self.domain_services.get_chatgpt_meal_suggestion()
        except Exception as e:
            logger.error(f"get_chatgpt_meal_suggestion error: {e}")
            suggestion = None
        from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
        if not suggestion:
            msg = (
                "申し訳ないです。おすすめを取得できませんでした。"
                " 管理者に OPENAI_API_KEY の設定を確認てもらってください。"
            )
            reply_message_request = ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=msg)]
            )
        else:
            reply_message_request = ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=suggestion)]
            )
        self.safe_reply_message(reply_message_request)

    def _handle_pokemon(self, event) -> None:
        """ポケモンリクエストを処理します"""
        logger.info("ポケモンリクエスト受信。図鑑風情報を返信")
        info = self._get_random_pokemon_zukan_info()
        if info:
            # create the bubble contents and wrap it as a Flex message object
            bubble_contents = create_pokemon_zukan_flex_dict(info)
            # Use a plain dict to represent the Flex message. Constructing the
            # SDK FlexMessage object may result in missing serialized fields
            # depending on SDK internals, so use the explicit dict matching the
            # LINE Messaging API contract.
            flex_msg_obj = {
                "type": "flex",
                "altText": "ポケモン図鑑",
                "contents": bubble_contents,
            }
            from linebot.v3.messaging.models import ReplyMessageRequest
            reply_message_request = ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[flex_msg_obj]
            )
            self.safe_reply_message(reply_message_request)
        else:
            from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
            reply_message_request = ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="ポケモン図鑑情報の取得に失敗しました。")]
            )
            self.safe_reply_message(reply_message_request)

    def _handle_chatgpt(self, event, text: str) -> None:
        """ChatGPTによる一般的な応答を処理します"""
        logger.info("コマンド以外のメッセージを受信: ChatGPT に問い合わせます")
        try:
            response = self.domain_services.get_chatgpt_response(text)
        except Exception as e:
            logger.error(f"get_chatgpt_response error: {e}")
            response = None
        from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
        if not response:
            msg = (
                "申し訳ないです。応答を生成できませんでした。"
                "管理者に OPENAI_API_KEY の設定を確認してもらってください。"
            )
            reply_message_request = ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=msg)]
            )
        else:
            reply_message_request = ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=response)]
            )
        self.safe_reply_message(reply_message_request)

    def _get_random_pokemon_zukan_info(self):
        """ランダムなポケモンの図鑑情報を取得します"""
        import random
        try:
            import requests
            # ランダムなポケモンを取得（1-1000の範囲）
            poke_id = random.randint(1, 1000)
            resp = requests.get(f'https://pokeapi.co/api/v2/pokemon/{poke_id}', timeout=10)
            resp.raise_for_status()
            data = resp.json()

            # 基本情報
            zukan_no = data['id']
            name_en = data['name']

            # 日本語名を取得
            name = name_en  # デフォルトは英語
            species_url = data.get('species', {}).get('url')
            if species_url:
                try:
                    species_resp = requests.get(species_url, timeout=10)
                    species_resp.raise_for_status()
                    species_data = species_resp.json()
                    for name_info in species_data.get('names', []):
                        if name_info.get('language', {}).get('name') == 'ja':
                            name = name_info.get('name')
                            break
                except Exception:
                    pass  # 日本語名取得失敗時は英語名を使用

            # タイプ
            types = [t['type']['name'] for t in data.get('types', [])]

            # 画像URL
            image_url = data.get('sprites', {}).get('other', {}).get('official-artwork', {}).get('front_default')

            # 進化情報（簡易版）
            evolution = "基本形"  # 簡易実装

            return {
                'zukan_no': zukan_no,
                'name': name,
                'types': types,
                'image_url': image_url,
                'evolution': evolution
            }
        except Exception as e:
            logger.error(f"ポケモン情報取得エラー: {e}")
            return None

    def _extract_location_from_weather_query(self, text: str) -> str:
        """天気クエリから地名を抽出します"""
        # 「○○の天気」パターンを検出
        import re
        match = re.search(r'(.+?)の天気', text)
        if match:
            location = match.group(1).strip()
            return location
        return ""



