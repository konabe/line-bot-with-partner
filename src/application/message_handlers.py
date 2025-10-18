import logging
from linebot.v3.messaging.models import TemplateMessage, ButtonsTemplate, PostbackAction
from typing import Protocol, Dict, Any, Callable
from src.infrastructure.line_model import create_pokemon_zukan_flex_dict
from src.domain import OpenAIClient

logger = logging.getLogger(__name__)


class DomainServices(Protocol):
    """Domain層サービスのインターフェース"""
    UMIGAME_STATE: Dict[str, Any]
    is_closed_question: Callable[[str], bool]
    generate_umigame_puzzle: Callable[[], Dict[str, str]]
    call_openai_yesno_with_secret: Callable[[str, str], str]
    get_chatgpt_meal_suggestion: Callable[[], str]
    get_chatgpt_response: Callable[[str], str]


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
        if t == 'ウミガメのスープ':
            return self._handle_umigame_start(event, user_id)
        if t == 'ウミガメのスープ終了':
            return self._handle_umigame_end(event, user_id)
        if user_id and self.domain_services.UMIGAME_STATE.get(user_id):
            if not self.domain_services.is_closed_question(text):
                logger.info('非クローズドクエスチョンをウミガメのスープモードで無視')
                return
            return self._handle_umigame_question(event, user_id, text)
        if t == '直接送信テスト':
            return self._handle_direct_send_test(event)
        if '天気' in text:
            return self._handle_weather(event, text)
        if t == 'じゃんけん':
            return self._handle_janken(event)
        if t == '今日のご飯':
            return self._handle_meal(event)
        if t == 'ポケモン':
            return self._handle_pokemon(event)
        return self._handle_chatgpt(event, text)

    def _handle_umigame_start(self, event, user_id: str) -> None:
        """ウミガメのスープモードを開始します"""
        if user_id:
            try:
                puzzle_obj = self.domain_services.generate_umigame_puzzle()
                self.domain_services.UMIGAME_STATE[user_id] = {'puzzle': puzzle_obj.get('puzzle', ''), 'answer': puzzle_obj.get('answer', '')}
                puzzle_text = self.domain_services.UMIGAME_STATE[user_id]['puzzle']
            except Exception as e:
                logger.error(f"failed to generate umigame puzzle: {e}")
                puzzle_text = '申し訳ないです。出題の生成に失敗しました。管理者に OPENAI_API_KEY の設定を確認してください。'
        else:
            puzzle_text = 'ウミガメのスープモードに入りました（ただし user_id が特定できないため内部状態は保持されません）。'
        from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
        reply_message_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=(
                f"ウミガメのスープモードに入りました。出題:\n{puzzle_text}\n\n"
                "クローズドクエスチョン（はい/いいえで答えられる質問）だけ受け付けます。"
                " 終了: 「ウミガメのスープ終了」"
            ))]
        )
        self.safe_reply_message(reply_message_request)

    def _handle_umigame_end(self, event, user_id: str) -> None:
        """ウミガメのスープモードを終了します"""
        if user_id and self.domain_services.UMIGAME_STATE.get(user_id):
            self.domain_services.UMIGAME_STATE.pop(user_id, None)
        from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
        reply_message_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text='ウミガメのスープモードを終了しました。')]
        )
        self.safe_reply_message(reply_message_request)

    def _handle_umigame_question(self, event, user_id: str, text: str) -> None:
        """ウミガメのスープモードでの質問を処理します"""
        try:
            secret = self.domain_services.UMIGAME_STATE[user_id].get('answer', '')
            answer = self.domain_services.call_openai_yesno_with_secret(text, secret)
        except Exception as e:
            logger.error(f"call_openai_yesno failed: {e}")
            from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
            reply_message_request = ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text='申し訳ないです。OpenAI の呼び出しに失敗しました。管理者に OPENAI_API_KEY の設定を確認してください。')]
            )
            self.safe_reply_message(reply_message_request)
            return
        cleared = False
        if answer.startswith('はい') or answer.startswith('はい、'):
            cleared = True
        from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
        reply_message_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=answer)]
        )
        self.safe_reply_message(reply_message_request)
        if cleared and user_id:
            self.domain_services.UMIGAME_STATE.pop(user_id, None)
            try:
                reply_message_request = ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text='おめでとうございます。核心に迫る質問が来たためウミガメのスープモードを終了します。')]
                )
                self.safe_reply_message(reply_message_request)
            except Exception:
                pass

    def _handle_direct_send_test(self, event) -> None:
        """直接送信テストを処理します"""
        logger.info("直接送信テストを受信: 対象ユーザーへ push 送信を試みます")
        user_id = None
        try:
            user_id = getattr(event.source, 'user_id', None) or getattr(event.source, 'userId', None)
        except Exception:
            user_id = None
        if not user_id:
            logger.error("user_id が取得できません。push を送信できません")
            from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
            reply_message_request = ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="直接送信ができませんでした: user_id が不明です")]
            )
            self.safe_reply_message(reply_message_request)
            return
        try:
            from datetime import datetime
            try:
                from zoneinfo import ZoneInfo
                now = datetime.now(ZoneInfo('Asia/Tokyo'))
            except Exception:
                now = datetime.now()
            now_str = now.strftime('%Y-%m-%d %H:%M:%S %Z')
        except Exception as e:
            logger.error(f"日時文字列作成に失敗: {e}")
            now_str = '取得できませんでした'
        from linebot.v3.messaging.models import PushMessageRequest, TextMessage
        push_message_request = PushMessageRequest(
            to=user_id,
            messages=[TextMessage(text=f"現在の日時: {now_str}")]
        )
        self.safe_reply_message(push_message_request)  # Note: This should be safe_push_message
        try:
            from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
            reply_message_request = ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="直接送信を行いました。")]
            )
            self.safe_reply_message(reply_message_request)
        except Exception:
            pass

    def _handle_weather(self, event, text: str) -> None:
        """天気リクエストを処理します"""
        logger.info("天気リクエスト検出")
        loc = self._extract_location_from_weather_query(text)
        if loc:
            logger.debug(f"位置解決: {loc}")
            reply_text = self._get_location_weather_text(loc)
        else:
            logger.debug("位置未指定のため博多天気を返す")
            reply_text = self._get_hakata_weather_text()
        from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
        reply_message_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=reply_text)]
        )
        self.safe_reply_message(reply_message_request)

    def _handle_janken(self, event) -> None:
        """じゃんけんリクエストを処理します"""
        logger.info("じゃんけんテンプレートを送信")
        template = TemplateMessage(
            alt_text="じゃんけんしましょう！",
            template=ButtonsTemplate(
                title="じゃんけん",
                text="どれを出しますか？",
                actions=[
                    PostbackAction(label="✊ グー", data="janken:✊"),
                    PostbackAction(label="✌️ チョキ", data="janken:✌️"),
                    PostbackAction(label="✋ パー", data="janken:✋")
                ]
            )
        )
        from linebot.v3.messaging.models import ReplyMessageRequest
        reply_message_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[template]
        )
        self.safe_reply_message(reply_message_request)

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

