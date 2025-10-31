import datetime
import json
import os
from typing import Optional
from zoneinfo import ZoneInfo

import requests
from openai import OpenAI

try:
    import promptlayer

    promptlayer_available = True
except ImportError:
    promptlayer_available = False

from ..logger import Logger, create_logger


class OpenAIError(Exception):
    pass


class OpenAIAdapter:
    OPENAI_API_KEY_ERROR = "OPENAI_API_KEY is not set"
    DEFAULT_MODEL = "gpt-5-mini"
    NO_CHOICES_ERROR = "no choices from OpenAI"

    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or create_logger(__name__)
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise OpenAIError(OpenAIAdapter.OPENAI_API_KEY_ERROR)
        self.model = os.environ.get("OPENAI_MODEL", OpenAIAdapter.DEFAULT_MODEL)

        # OpenAI クライアントを初期化
        self.openai_client = OpenAI(api_key=self.api_key)

        # PromptLayerの設定
        self.promptlayer_api_key = os.environ.get("PROMPTLAYER_API_KEY")
        self.promptlayer_client = None
        if self.promptlayer_api_key and promptlayer_available:
            try:
                # PromptLayer クライアントを初期化
                self.promptlayer_client = promptlayer.PromptLayer(
                    api_key=self.promptlayer_api_key
                )
                self.use_promptlayer = True
                self.logger.info("PromptLayer enabled")
            except Exception as e:
                self.logger.warning(
                    f"Failed to initialize PromptLayer: {e}. PromptLayer logging will be disabled."
                )
                self.use_promptlayer = False
        else:
            self.use_promptlayer = False
            if not self.promptlayer_api_key:
                self.logger.info("PromptLayer disabled (PROMPTLAYER_API_KEY not set)")
            elif not promptlayer_available:
                self.logger.info(
                    "PromptLayer disabled (promptlayer package not installed)"
                )

    def _call_openai_api(
        self, messages: list, pl_tags: Optional[list[str]] = None
    ) -> str:
        """OpenAI SDK + PromptLayerを使ってAPIを呼び出す"""
        try:
            self.logger.debug(
                f"OpenAI request: model={self.model}, messages={json.dumps(messages, ensure_ascii=False)}"
            )
        except Exception:
            pass

        try:
            # OpenAI SDKで呼び出し
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=3000,
            )

            content = response.choices[0].message.content
            if not content:
                raise OpenAIError(OpenAIAdapter.NO_CHOICES_ERROR)

            # PromptLayerにログを送信
            if self.use_promptlayer and self.promptlayer_client:
                try:
                    self.logger.debug("Logging to PromptLayer")
                    pl_payload = {
                        "function_name": "openai.chat.completions.create",
                        "provider_type": "openai",
                        "args": [],
                        "kwargs": {
                            "model": self.model,
                            "messages": messages,
                            "max_completion_tokens": 3000,
                        },
                        "tags": pl_tags or [],
                        "request_response": response.model_dump(),
                        "request_start_time": 0,
                        "request_end_time": 0,
                        "api_key": self.promptlayer_api_key,
                    }

                    pl_resp = requests.post(
                        "https://api.promptlayer.com/rest/track-request",
                        json=pl_payload,
                        headers={"Content-Type": "application/json"},
                        timeout=5,
                    )

                    if pl_resp.status_code == 200:
                        self.logger.debug("Successfully logged to PromptLayer")
                    else:
                        self.logger.warning(
                            f"PromptLayer returned status {pl_resp.status_code}: {pl_resp.text}"
                        )
                except Exception as e:
                    self.logger.warning(f"Failed to log to PromptLayer: {e}")

            return content.strip()
        except OpenAIError:
            raise
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            raise OpenAIError(f"OpenAI API error: {str(e)}") from e

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
