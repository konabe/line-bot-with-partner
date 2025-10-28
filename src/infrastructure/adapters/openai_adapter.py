import os
import requests
import datetime
import json
from zoneinfo import ZoneInfo
from typing import Optional

from ..logger import Logger, create_logger


class OpenAIError(Exception):
    """汎用的な OpenAI 関連の例外クラス

    ユースケースやハンドラ側はこの例外をキャッチすることで、OpenAI に起因する失敗を識別できます。
    """


class OpenAIAdapter:
    """OpenAI APIとの通信を担当するアダプタクラス"""

    # 定数定義
    OPENAI_API_KEY_ERROR = "OPENAI_API_KEY is not set"
    DEFAULT_MODEL = "gpt-5-mini"
    CONTENT_TYPE_JSON = "application/json"
    OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
    NO_CHOICES_ERROR = "no choices from OpenAI"

    def __init__(self, logger: Optional[Logger] = None):
        """OpenAIAdapterの初期化

        Args:
            logger: DI 可能な Logger。指定がない場合は標準のロガーを作成します。
        """
        self.logger = logger or create_logger(__name__)
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            # 明示的な例外型で統一する
            raise OpenAIError(OpenAIAdapter.OPENAI_API_KEY_ERROR)
        self.model = os.environ.get("OPENAI_MODEL", OpenAIAdapter.DEFAULT_MODEL)

    def get_chatgpt_meal_suggestion(self):
        """料理のおすすめをChatGPTから取得"""
        now = datetime.datetime.now(ZoneInfo("Asia/Tokyo"))
        now_str = now.strftime("%Y-%m-%d %H:%M")
        prompt = (
            f"現在の日時は {now_str} です。これを参考に、"
            "あなたは親切な料理アドバイザーです。ユーザーに今すぐ作れる料理のおすすめを3つ、"
            "簡単なレシピや調理時間（目安）と一言コメント付きで提案してください。日本語で答えてください。"
        )
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_completion_tokens": 3000,
        }
        try:
            # ログはペイロードのみ（APIキー等のヘッダは出力しない）
            try:
                self.logger.debug(
                    f"OpenAI request payload: {json.dumps(payload, ensure_ascii=False)}"
                )
            except Exception:
                # payload が JSON 化できない場合は無視
                pass

            resp = requests.post(
                OpenAIAdapter.OPENAI_API_URL, json=payload, headers=headers, timeout=30
            )
            # 詳細なエラーボディをログに残す（400系含む）
            if resp.status_code >= 400:
                # レスポンス本文をログに残すが、過度に長い場合は切り詰める
                body = resp.text or ""
                if len(body) > 2000:
                    body = body[:2000] + "...[truncated]"
                self.logger.error(f"OpenAI returned status {resp.status_code}: {body}")
                raise OpenAIError(f"OpenAI error {resp.status_code}: {body}")

            data = resp.json()

            choices = data.get("choices", [])
            if not choices:
                raise OpenAIError(OpenAIAdapter.NO_CHOICES_ERROR)

            message = choices[0].get("message", {})
            content = message.get("content", "")
            if not content:
                raise OpenAIError(OpenAIAdapter.NO_CHOICES_ERROR)
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
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "max_completion_tokens": 3000,
        }
        try:
            try:
                self.logger.debug(
                    f"OpenAI request payload: {json.dumps(payload, ensure_ascii=False)}"
                )
            except Exception:
                pass

            resp = requests.post(
                OpenAIAdapter.OPENAI_API_URL, json=payload, headers=headers, timeout=30
            )
            if resp.status_code >= 400:
                body = resp.text or ""
                if len(body) > 2000:
                    body = body[:2000] + "...[truncated]"
                self.logger.error(f"OpenAI returned status {resp.status_code}: {body}")
                raise OpenAIError(f"OpenAI error {resp.status_code}: {body}")

            data = resp.json()

            choices = data.get("choices", [])
            if not choices:
                raise OpenAIError(OpenAIAdapter.NO_CHOICES_ERROR)

            message = choices[0].get("message", {})
            content = message.get("content", "")
            if not content:
                raise OpenAIError(OpenAIAdapter.NO_CHOICES_ERROR)
            return content.strip()
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            raise OpenAIError(str(e)) from e
