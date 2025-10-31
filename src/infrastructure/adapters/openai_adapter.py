import datetime
import json
import os
from typing import Optional
from zoneinfo import ZoneInfo

import requests

try:
    import promptlayer
except ImportError:
    promptlayer = None  # type: ignore

from ..logger import Logger, create_logger


class OpenAIError(Exception):
    pass


class OpenAIAdapter:
    OPENAI_API_KEY_ERROR = "OPENAI_API_KEY is not set"
    DEFAULT_MODEL = "gpt-5-mini"
    CONTENT_TYPE_JSON = "application/json"
    OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
    NO_CHOICES_ERROR = "no choices from OpenAI"

    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or create_logger(__name__)
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise OpenAIError(OpenAIAdapter.OPENAI_API_KEY_ERROR)
        self.model = os.environ.get("OPENAI_MODEL", OpenAIAdapter.DEFAULT_MODEL)

        # PromptLayerの設定
        self.promptlayer_api_key = os.environ.get("PROMPTLAYER_API_KEY")
        if self.promptlayer_api_key and promptlayer:
            self.promptlayer_client = promptlayer.PromptLayer(
                api_key=self.promptlayer_api_key
            )
            self.use_promptlayer = True
            self.logger.info("PromptLayer enabled")
        else:
            self.promptlayer_client = None
            self.use_promptlayer = False
            if self.promptlayer_api_key and not promptlayer:
                self.logger.warning(
                    "promptlayer package not installed, disabling PromptLayer"
                )
            else:
                self.logger.info("PromptLayer disabled (PROMPTLAYER_API_KEY not set)")

    def _log_to_promptlayer(
        self, request_payload: dict, response_data: dict, pl_tags: list[str]
    ) -> None:
        """PromptLayerにログを送信"""
        if not self.use_promptlayer:
            return

        try:
            pl_request = {
                "function_name": "openai.ChatCompletion.create",
                "kwargs": request_payload,
                "tags": pl_tags,
                "request_response": response_data,
                "request_start_time": datetime.datetime.now(
                    ZoneInfo("UTC")
                ).timestamp(),
                "request_end_time": datetime.datetime.now(ZoneInfo("UTC")).timestamp(),
            }

            pl_headers = {"X-API-KEY": self.promptlayer_api_key}

            requests.post(
                "https://api.promptlayer.com/track-request",
                json=pl_request,
                headers=pl_headers,
                timeout=5,
            )
        except Exception as e:
            self.logger.warning(f"Failed to log to PromptLayer: {e}")

    def _call_openai_api(
        self, messages: list, pl_tags: Optional[list[str]] = None
    ) -> str:
        """OpenAI APIを呼び出す（PromptLayer対応）"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
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
                OpenAIAdapter.OPENAI_API_URL,
                json=payload,
                headers=headers,
                timeout=30,
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

            # PromptLayerにログを送信
            self._log_to_promptlayer(payload, data, pl_tags or [])

            return content.strip()
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            raise OpenAIError(str(e)) from e

    def get_chatgpt_meal_suggestion(self):
        now = datetime.datetime.now(ZoneInfo("Asia/Tokyo"))
        now_str = now.strftime("%Y-%m-%d %H:%M")
        prompt = (
            f"現在の日時は {now_str} です。これを参考に、"
            "あなたは親切な料理アドバイザーです。ユーザーに今すぐ作れる料理のおすすめを3つ、"
            "簡単なレシピや調理時間（目安）と一言コメント付きで提案してください。日本語で答えてください。"
        )
        messages = [{"role": "user", "content": prompt}]
        return self._call_openai_api(messages, pl_tags=["meal_suggestion"])

    def get_chatgpt_response(self, user_message: str) -> str:
        system_prompt = (
            "あなたは群馬県のマスコットキャラクターの「ぐんまちゃん」です。ユーザーのメッセージに対して、"
            "親しみやすく、時にはユーモアを交えて返答してください。"
            "話を広げるように心がけ、ユーザーとの会話を楽しんでください。"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        return self._call_openai_api(messages, pl_tags=["chat_response"])
