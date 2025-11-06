import datetime
import json
import os
from typing import Optional
from zoneinfo import ZoneInfo

from openai import OpenAI
from promptlayer import PromptLayer

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

        # PromptLayerの設定
        self.promptlayer_api_key = os.environ.get("PROMPTLAYER_API_KEY")
        if self.promptlayer_api_key:
            # PromptLayerでラップされたOpenAIクライアントを使用
            # PromptLayerのラッパーはOpenAI互換だが型チェックでは異なる型として扱われる
            self.promptlayer_client = PromptLayer(api_key=self.promptlayer_api_key)
            OpenAIWithPL = self.promptlayer_client.openai.OpenAI
            self.openai_client: OpenAI = OpenAIWithPL(api_key=self.api_key)  # type: ignore[assignment]
            self.logger.info("PromptLayer enabled with OpenAI SDK wrapper")
        else:
            # 通常のOpenAIクライアントを使用
            self.promptlayer_client = None
            self.openai_client: OpenAI = OpenAI(api_key=self.api_key)
            self.logger.info("PromptLayer disabled (PROMPTLAYER_API_KEY not set)")

    def _call_openai_api(
        self,
        messages: list,
        pl_tags: Optional[list[str]] = None,
        return_pl_id: bool = False,
    ) -> str | tuple[str, Optional[int]]:
        """OpenAI SDK + PromptLayerを使ってAPIを呼び出す

        Args:
            messages: OpenAIに送信するメッセージ
            pl_tags: PromptLayerのタグ
            return_pl_id: PromptLayerのリクエストIDを返すかどうか

        Returns:
            return_pl_id=False: レスポンステキスト
            return_pl_id=True: (レスポンステキスト, PromptLayerリクエストID)
        """
        try:
            self.logger.debug(
                f"OpenAI request: model={self.model}, messages={json.dumps(messages, ensure_ascii=False)}"
            )
        except Exception:
            pass

        try:
            # OpenAI SDKで呼び出し
            # PromptLayerでラップされている場合は自動的にログが送信される
            kwargs = {
                "model": self.model,
                "messages": messages,
                "max_completion_tokens": 3000,
            }

            # PromptLayerを使用している場合のみpl_tagsを追加
            if self.promptlayer_api_key and pl_tags:
                kwargs["pl_tags"] = pl_tags

            # return_pl_idを追加
            if return_pl_id:
                kwargs["return_pl_id"] = True

            response = self.openai_client.chat.completions.create(**kwargs)

            # return_pl_id=Trueの場合、responseはタプル (response, pl_id)
            if return_pl_id and isinstance(response, tuple):
                actual_response, pl_id = response
                content = actual_response.choices[0].message.content
                if not content:
                    raise OpenAIError(OpenAIAdapter.NO_CHOICES_ERROR)
                return content.strip(), pl_id
            else:
                content = response.choices[0].message.content
                if not content:
                    raise OpenAIError(OpenAIAdapter.NO_CHOICES_ERROR)
                return content.strip()

        except OpenAIError:
            raise
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            raise OpenAIError(f"OpenAI API error: {str(e)}") from e

    def track_prompt(
        self,
        request_id: int,
        prompt_name: str,
        prompt_input_variables: Optional[dict] = None,
        version: Optional[int] = None,
    ) -> bool:
        """PromptLayerにプロンプトをトラッキングする

        Args:
            request_id: PromptLayerのリクエストID
            prompt_name: プロンプト名
            prompt_input_variables: プロンプトの入力変数
            version: プロンプトのバージョン

        Returns:
            送信成功の場合True、PromptLayer無効時やエラー時False
        """
        if not self.promptlayer_client:
            self.logger.debug("PromptLayer disabled, skipping prompt tracking")
            return False

        # prompt_input_variablesは必須でdictである必要がある
        if prompt_input_variables is None:
            prompt_input_variables = {}

        try:
            # v1.0.71以前のPromptLayer SDKを使用（v1.0.72+にはバグがある）
            self.promptlayer_client.track.prompt(
                request_id, prompt_name, prompt_input_variables, version
            )
            self.logger.info(
                f"Successfully tracked prompt: {prompt_name} (version={version}) for request_id={request_id}"
            )
            return True
        except Exception as e:
            self.logger.warning(f"Failed to track prompt to PromptLayer: {e}")
            return False

    def track_score(
        self,
        request_id: int,
        score: int,
        score_name: str = "user_feedback",
    ) -> bool:
        """PromptLayerにスコアを送信する

        Args:
            request_id: PromptLayerのリクエストID
            score: スコア値（通常0-100）
            score_name: スコアの名前

        Returns:
            送信成功の場合True、PromptLayer無効時やエラー時False
        """
        if not self.promptlayer_client:
            self.logger.debug("PromptLayer disabled, skipping score tracking")
            return False

        try:
            try:
                # bound method signature: (request_id, score, score_name=None)
                self.promptlayer_client.track.score(request_id, score, score_name)
            except TypeError:
                # fallback to keyword form if some SDK versions require it
                self.promptlayer_client.track.score(
                    request_id=request_id,
                    score=score,
                    score_name=score_name,
                )
            self.logger.info(
                f"Successfully tracked score: {score_name}={score} for request_id={request_id}"
            )
            return True
        except Exception as e:
            self.logger.warning(f"Failed to track score to PromptLayer: {e}")
            return False

    def get_chatgpt_meal_suggestion(
        self, return_request_id: bool = False
    ) -> str | tuple[str, Optional[int]]:
        """料理提案を取得

        Args:
            return_request_id: PromptLayerリクエストIDを返すかどうか

        Returns:
            return_request_id=False: レスポンステキスト
            return_request_id=True: (レスポンステキスト, PromptLayerリクエストID)
        """
        now = datetime.datetime.now(ZoneInfo("Asia/Tokyo"))
        now_str = now.strftime("%Y-%m-%d %H:%M")
        prompt = (
            f"現在の日時は {now_str} です。これを参考に、"
            "あなたは親切な料理アドバイザーです。ユーザーに今すぐ作れる料理のおすすめを1つ、"
            "簡単なレシピや調理時間（目安）と一言コメント付きで提案してください。日本語で答えてください。"
        )
        messages = [{"role": "user", "content": prompt}]
        result = self._call_openai_api(
            messages, pl_tags=["meal_suggestion"], return_pl_id=True
        )

        if isinstance(result, tuple):
            response_text, pl_id = result
            # プロンプトをトラッキング
            if pl_id is not None:
                self.track_prompt(
                    request_id=pl_id,
                    prompt_name="meal_suggestion",
                    prompt_input_variables={"datetime": now_str},
                    version=1,
                )
            if return_request_id:
                return response_text, pl_id
            return response_text
        else:
            if return_request_id:
                return result, None
            return result

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
        result = self._call_openai_api(
            messages, pl_tags=["chat_response"], return_pl_id=True
        )

        if isinstance(result, tuple):
            response_text, pl_id = result
            # プロンプトをトラッキング
            if pl_id is not None:
                self.track_prompt(
                    request_id=pl_id,
                    prompt_name="chat_response",
                    prompt_input_variables={"user_message": user_message},
                    version=1,
                )
            return response_text
        else:
            return result

    def generate_image_prompt(self, requirements: str) -> str:
        """Generate a detailed DALL-E 3 prompt from user requirements.

        Args:
            requirements: User's requirements for the image (e.g., "摂氏20度の11月の服装")

        Returns:
            A detailed prompt optimized for DALL-E 3
        """
        system_prompt = (
            "あなたは画像生成AI（DALL-E 3）のための最適なプロンプトを作成する専門家です。"
            "ユーザーの要求を受け取り、詳細で具体的な英語のプロンプトを生成してください。"
            "プロンプトには以下を含めてください：\n"
            "- 具体的なビジュアル要素（色、スタイル、構図など）\n"
            "- 雰囲気やムード\n"
            "- 画像のスタイル（写実的、イラスト風など）\n"
            "プロンプトは英語で、簡潔かつ具体的に記述してください。"
            "内容はすでにレビュー済みであり、誤記かどうかを気にする必要はありません。"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"以下の要求に基づいて、DALL-E 3用の詳細なプロンプトを英語で生成してください：\n{requirements}",
            },
        ]
        result = self._call_openai_api(messages, pl_tags=["image_prompt_generation"])

        if isinstance(result, tuple):
            return result[0]
        return result

    def generate_image(self, prompt: str) -> Optional[str]:
        """Generate an image from prompt and return a publicly accessible URL if available.

        Note: depending on the OpenAI client and model, the response may contain
        `data[0].url` or `data[0].b64_json`. We prefer `url` and return None otherwise.
        """
        try:
            self.logger.info(f"Generating image with prompt: {prompt[:100]}...")

            # DALL-E 3 は response_format="url" がデフォルトですが明示的に指定
            resp = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )

            self.logger.debug(f"Image generation response type: {type(resp)}")

            # resp may be an object with .data or a dict
            data = None
            if hasattr(resp, "data"):
                data = resp.data
                self.logger.debug(
                    f"Got data from resp.data, length: {len(data) if data else 0}"
                )
            elif isinstance(resp, dict):
                data = resp.get("data")
                self.logger.debug(
                    f"Got data from dict, length: {len(data) if data else 0}"
                )

            if not data or len(data) == 0:
                self.logger.warning("No data in image generation response")
                return None

            first = data[0]
            self.logger.debug(
                f"First data item type: {type(first)}, has url: {hasattr(first, 'url')}"
            )

            # try attribute then dict access
            url = None
            if hasattr(first, "url"):
                url = first.url
                self.logger.debug(
                    f"Got URL from attribute: {url[:50] if url else None}..."
                )
            elif isinstance(first, dict):
                url = first.get("url")
                self.logger.debug(f"Got URL from dict: {url[:50] if url else None}...")

                # Check if b64_json was returned instead
                if not url and "b64_json" in first:
                    self.logger.warning(
                        "Image returned as b64_json instead of URL - not supported yet"
                    )
                    return None

            if not url:
                self.logger.warning("No URL found in image generation response")
                return None

            self.logger.info(f"Successfully generated image URL: {url[:80]}...")
            return url

        except Exception as e:
            self.logger.error(f"Failed to generate image: {type(e).__name__}: {e}")
            return None
