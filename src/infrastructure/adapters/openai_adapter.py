import datetime
import json
import os
import time
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
        if self.promptlayer_api_key:
            self.use_promptlayer = True
            self.logger.info("PromptLayer enabled")
        else:
            self.use_promptlayer = False
            self.logger.info("PromptLayer disabled (PROMPTLAYER_API_KEY not set)")

    def _log_to_promptlayer(
        self,
        request_payload: dict,
        response_data: dict,
        pl_tags: list[str],
        request_start_time: float,
        request_end_time: float,
    ) -> None:
        """PromptLayerにログを送信（REST API経由）"""
        if not self.use_promptlayer:
            return

        try:
            # PromptLayer REST APIにログを送信
            pl_request = {
                "function_name": "openai.chat.completions.create",
                "provider_type": "openai",
                "args": [],
                "kwargs": request_payload,
                "tags": pl_tags,
                "request_response": response_data,
                "request_start_time": request_start_time,
                "request_end_time": request_end_time,
                "api_key": self.promptlayer_api_key,
            }

            self.logger.debug(
                f"Sending log to PromptLayer: {json.dumps(pl_request, ensure_ascii=False, default=str)}"
            )

            response = requests.post(
                "https://api.promptlayer.com/rest/track-request",
                json=pl_request,
                timeout=5,
            )

            if response.status_code == 200:
                self.logger.debug(
                    f"Successfully logged to PromptLayer with tags: {pl_tags}"
                )
            else:
                self.logger.warning(
                    f"PromptLayer returned status {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.logger.warning(f"Failed to log to PromptLayer: {e}")

    def _call_openai_api(
        self, messages: list, pl_tags: Optional[list[str]] = None
    ) -> str:
        """OpenAI APIを呼び出す（PromptLayer対応）"""
        request_start_time = time.time()

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
            request_end_time = time.time()

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
            self._log_to_promptlayer(
                payload, data, pl_tags or [], request_start_time, request_end_time
            )

            return content.strip()
        except OpenAIError:
            # 既にOpenAIErrorの場合はそのまま再raise（二重ラップを防ぐ）
            raise
        except requests.exceptions.RequestException as e:
            # ネットワークエラー
            self.logger.error(f"OpenAI API network error: {e}")
            raise OpenAIError(f"Network error: {str(e)}") from e
        except Exception as e:
            # その他の予期しないエラー
            self.logger.error(f"Unexpected error in OpenAI API call: {e}")
            raise OpenAIError(f"Unexpected error: {str(e)}") from e

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
