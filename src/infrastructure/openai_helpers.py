import os
import re
import requests
import datetime
from zoneinfo import ZoneInfo
from typing import Optional

from .logger import Logger, create_logger


class OpenAIError(Exception):
    """汎用的な OpenAI 関連の例外クラス

    ユースケースやハンドラ側はこの例外をキャッチすることで、OpenAI に起因する失敗を識別できます。
    """


class OpenAIClient:
    """OpenAI APIとの通信を担当するクライアントクラス"""

    # 定数定義
    OPENAI_API_KEY_ERROR = 'OPENAI_API_KEY is not set'
    DEFAULT_MODEL = 'gpt-5'
    CONTENT_TYPE_JSON = 'application/json'
    # GPT-5 Responses API endpoint
    OPENAI_API_URL = 'https://api.openai.com/v1/responses'
    NO_CHOICES_ERROR = 'no choices from OpenAI'

    def __init__(self, logger: Optional[Logger] = None):
        """OpenAIClientの初期化

        Args:
            logger: DI 可能な Logger。指定がない場合は標準のロガーを作成します。
        """
        self.logger = logger or create_logger(__name__)
        self.api_key = os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            # 明示的な例外型で統一する
            raise OpenAIError(OpenAIClient.OPENAI_API_KEY_ERROR)
        self.model = os.environ.get('OPENAI_MODEL', OpenAIClient.DEFAULT_MODEL)

    def get_chatgpt_meal_suggestion(self):
        """料理のおすすめをChatGPTから取得"""
        # 現在日時を取得してプロンプトに含める（提案内容を時間帯に合わせる手がかりにする）
        # 東京タイムゾーンで現在日時を取得してプロンプトに含める
        now = datetime.datetime.now(ZoneInfo("Asia/Tokyo"))
        now_str = now.strftime('%Y-%m-%d %H:%M')
        prompt = (
            f"現在の日時は {now_str} です。これを参考に、"
            "あなたは親切な料理アドバイザーです。ユーザーに今すぐ作れる料理のおすすめを3つ、"
            "簡単なレシピや調理時間（目安）と一言コメント付きで提案してください。日本語で答えてください。"
        )
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            "Content-Type": "application/json"
        }
        # Responses API uses `input` (or `messages`) and may return different shapes.
        payload = {
            'model': self.model,
            'input': prompt,
            'max_output_tokens': 500,
            'temperature': 0.8,
        }
        try:
            resp = requests.post(OpenAIClient.OPENAI_API_URL, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            # 抽出の互換性を広く持たせる
            def _extract_text_from_response(data: dict) -> str:
                choices = data.get('choices') or []
                if choices:
                    choice = choices[0]
                    # message.content
                    msg = choice.get('message')
                    if msg:
                        content = msg.get('content')
                        if isinstance(content, str):
                            return content
                        if isinstance(content, list):
                            parts = []
                            for c in content:
                                if isinstance(c, str):
                                    parts.append(c)
                                elif isinstance(c, dict):
                                    parts.append(c.get('text') or c.get('content') or '')
                            if parts:
                                return ''.join(parts)
                    # choice.text
                    if isinstance(choice.get('text'), str):
                        return choice.get('text')
                    if choice.get('output_text'):
                        return choice.get('output_text')

                # Responses API: top-level "output" can be str or list
                out = data.get('output')
                if isinstance(out, str):
                    return out
                if isinstance(out, list):
                    parts = []
                    for o in out:
                        if isinstance(o, str):
                            parts.append(o)
                        elif isinstance(o, dict):
                            # dict may contain 'content' list
                            c = o.get('content')
                            if isinstance(c, list):
                                for e in c:
                                    if isinstance(e, str):
                                        parts.append(e)
                                    elif isinstance(e, dict):
                                        parts.append(e.get('text') or e.get('content') or '')
                    if parts:
                        return ''.join(parts)

                # fallback
                return ''

            content = _extract_text_from_response(data)
            if not content:
                raise OpenAIError(OpenAIClient.NO_CHOICES_ERROR)
            return content
        except Exception as e:
            # ここでは OpenAI に起因する任意の例外を OpenAIError にラップして投げる
            self.logger.error(f"OpenAI API error: {e}")
            raise OpenAIError(str(e)) from e

    def get_chatgpt_response(self, user_message: str) -> str:
        """ユーザーのメッセージに対してChatGPTを使って返答を生成"""
        system_prompt = (
            "あなたは群馬県のマスコットキャラクターの「ぐんまちゃん」です。ユーザーのメッセージに対して、"
            "親しみやすく、時にはユーモアを交えて返答してください。"
            "話を広げるように心がけ、ユーザーとの会話を楽しんでください。"
        )
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            "Content-Type": "application/json"
        }
        payload = {
            'model': self.model,
            'instruction': f"{system_prompt}",
            'input': f"{user_message}",
            'max_output_tokens': 500,
            'temperature': 0.7,
        }
        try:
            resp = requests.post(OpenAIClient.OPENAI_API_URL, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            # reuse extraction logic
            def _extract_text_from_response(data: dict) -> str:
                choices = data.get('choices') or []
                if choices:
                    choice = choices[0]
                    msg = choice.get('message')
                    if msg:
                        content = msg.get('content')
                        if isinstance(content, str):
                            return content
                        if isinstance(content, list):
                            parts = []
                            for c in content:
                                if isinstance(c, str):
                                    parts.append(c)
                                elif isinstance(c, dict):
                                    parts.append(c.get('text') or c.get('content') or '')
                            if parts:
                                return ''.join(parts)
                    if isinstance(choice.get('text'), str):
                        return choice.get('text')
                    if choice.get('output_text'):
                        return choice.get('output_text')

                out = data.get('output')
                if isinstance(out, str):
                    return out
                if isinstance(out, list):
                    parts = []
                    for o in out:
                        if isinstance(o, str):
                            parts.append(o)
                        elif isinstance(o, dict):
                            c = o.get('content')
                            if isinstance(c, list):
                                for e in c:
                                    if isinstance(e, str):
                                        parts.append(e)
                                    elif isinstance(e, dict):
                                        parts.append(e.get('text') or e.get('content') or '')
                    if parts:
                        return ''.join(parts)
                return ''

            content = _extract_text_from_response(data)
            if not content:
                raise OpenAIError(OpenAIClient.NO_CHOICES_ERROR)
            return content.strip()
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            raise OpenAIError(str(e)) from e
