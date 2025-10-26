import os
import re
import requests
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
    DEFAULT_MODEL = 'gpt-5-mini'
    CONTENT_TYPE_JSON = 'application/json'
    OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions'
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
        prompt = (
            "あなたは親切な料理アドバイザーです。ユーザーに今すぐ作れる料理のおすすめを3つ、"
            "簡単なレシピや調理時間（目安）と一言コメント付きで提案してください。日本語で答えてください。"
        )
        headers = {
            OpenAIClient.CONTENT_TYPE_JSON: OpenAIClient.CONTENT_TYPE_JSON,
            'Authorization': f'Bearer {self.api_key}'
        }
        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': 'あなたは家庭料理に詳しいアドバイザーです。'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 500,
            'temperature': 0.8,
        }
        try:
            resp = requests.post(OpenAIClient.OPENAI_API_URL, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            choices = data.get('choices') or []
            if not choices:
                raise OpenAIError(OpenAIClient.NO_CHOICES_ERROR)
            content = choices[0].get('message', {}).get('content')
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
            OpenAIClient.CONTENT_TYPE_JSON: OpenAIClient.CONTENT_TYPE_JSON,
            'Authorization': f'Bearer {self.api_key}'
        }
        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message}
            ],
            'max_tokens': 1000,
            'temperature': 0.7,
        }
        try:
            resp = requests.post(OpenAIClient.OPENAI_API_URL, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            choices = data.get('choices') or []
            if not choices:
                raise OpenAIError(OpenAIClient.NO_CHOICES_ERROR)
            content = choices[0].get('message', {}).get('content')
            return content.strip()
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            raise OpenAIError(str(e)) from e
