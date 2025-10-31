"""OpenAIAdapter のテスト"""

from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.adapters.openai_adapter import OpenAIAdapter, OpenAIError


class TestOpenAIAdapter:
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test_api_key"}, clear=True)
    def test_init_with_api_key(self):
        """環境変数にAPI Keyがある場合、正常に初期化できること"""
        adapter = OpenAIAdapter()

        assert adapter.api_key == "test_api_key"
        assert adapter.model == "gpt-5-mini"  # デフォルトモデル
        assert adapter.use_promptlayer is False  # PROMPTLAYER_API_KEYがないのでFalse

    @patch.dict(
        "os.environ",
        {"OPENAI_API_KEY": "test_api_key", "OPENAI_MODEL": "gpt-4"},
        clear=True,
    )
    def test_init_with_custom_model(self):
        """カスタムモデルを指定できること"""
        adapter = OpenAIAdapter()

        assert adapter.api_key == "test_api_key"
        assert adapter.model == "gpt-4"

    @patch.dict(
        "os.environ",
        {
            "OPENAI_API_KEY": "test_api_key",
            "PROMPTLAYER_API_KEY": "test_promptlayer_key",
        },
        clear=True,
    )
    @patch("src.infrastructure.adapters.openai_adapter.promptlayer_available", True)
    @patch("src.infrastructure.adapters.openai_adapter.promptlayer")
    def test_init_with_promptlayer(self, mock_promptlayer):
        """PROMPTLAYER_API_KEYがある場合、PromptLayerが有効になること"""
        mock_openai_client = MagicMock()
        mock_promptlayer.openai.OpenAI.return_value = mock_openai_client

        adapter = OpenAIAdapter()

        assert adapter.use_promptlayer is True
        assert adapter.promptlayer_api_key == "test_promptlayer_key"
        assert adapter.openai_client is mock_openai_client

    @patch.dict("os.environ", {}, clear=True)
    def test_init_without_api_key(self):
        """環境変数にAPI Keyがない場合、エラーが発生すること"""
        with pytest.raises(OpenAIError) as excinfo:
            OpenAIAdapter()

        assert "OPENAI_API_KEY is not set" in str(excinfo.value)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test_api_key"}, clear=True)
    def test_init_with_logger(self):
        """loggerを指定してインスタンス化できること"""
        mock_logger = MagicMock()
        adapter = OpenAIAdapter(logger=mock_logger)

        assert adapter.logger == mock_logger

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test_api_key"}, clear=True)
    @patch("requests.post")
    def test_get_chatgpt_meal_suggestion_success(self, mock_post):
        """料理提案を正常に取得できること（PromptLayerなし）"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "1. カレーライス（調理時間: 30分）\n2. オムライス（調理時間: 20分）\n3. チャーハン（調理時間: 15分）"
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        adapter = OpenAIAdapter()
        result = adapter.get_chatgpt_meal_suggestion()

        assert "カレーライス" in result
        assert mock_post.call_count == 1
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.openai.com/v1/chat/completions"
        assert call_args[1]["json"]["model"] == "gpt-5-mini"
        assert "料理アドバイザー" in call_args[1]["json"]["messages"][0]["content"]

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test_api_key"}, clear=True)
    @patch("requests.post")
    def test_get_chatgpt_response_success(self, mock_post):
        """チャット応答を正常に取得できること（PromptLayerなし）"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "こんにちは！ぐんまちゃんだよ！"}}]
        }
        mock_post.return_value = mock_response

        adapter = OpenAIAdapter()
        result = adapter.get_chatgpt_response("こんにちは")

        assert result == "こんにちは！ぐんまちゃんだよ！"
        assert mock_post.call_count == 1
        call_args = mock_post.call_args
        assert call_args[1]["json"]["messages"][0]["role"] == "system"
        assert "ぐんまちゃん" in call_args[1]["json"]["messages"][0]["content"]
        assert call_args[1]["json"]["messages"][1]["role"] == "user"
        assert call_args[1]["json"]["messages"][1]["content"] == "こんにちは"

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test_api_key"}, clear=True)
    @patch("requests.post")
    def test_get_chatgpt_meal_suggestion_api_error(self, mock_post):
        """APIがエラーを返した場合、OpenAIErrorが発生すること"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        adapter = OpenAIAdapter()
        with pytest.raises(OpenAIError) as excinfo:
            adapter.get_chatgpt_meal_suggestion()

        assert "500" in str(excinfo.value)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test_api_key"}, clear=True)
    @patch("requests.post")
    def test_get_chatgpt_response_api_error(self, mock_post):
        """APIがエラーを返した場合、OpenAIErrorが発生すること"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        adapter = OpenAIAdapter()
        with pytest.raises(OpenAIError) as excinfo:
            adapter.get_chatgpt_response("テスト")

        assert "401" in str(excinfo.value)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test_api_key"}, clear=True)
    @patch("requests.post")
    def test_get_chatgpt_meal_suggestion_no_choices(self, mock_post):
        """APIレスポンスにchoicesがない場合、エラーが発生すること"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": []}
        mock_post.return_value = mock_response

        adapter = OpenAIAdapter()
        with pytest.raises(OpenAIError) as excinfo:
            adapter.get_chatgpt_meal_suggestion()

        assert "no choices from OpenAI" in str(excinfo.value)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test_api_key"}, clear=True)
    @patch("requests.post")
    def test_get_chatgpt_response_empty_content(self, mock_post):
        """APIレスポンスのcontentが空の場合、エラーが発生すること"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": ""}}]}
        mock_post.return_value = mock_response

        adapter = OpenAIAdapter()
        with pytest.raises(OpenAIError) as excinfo:
            adapter.get_chatgpt_response("テスト")

        assert "no choices from OpenAI" in str(excinfo.value)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test_api_key"}, clear=True)
    @patch("requests.post")
    def test_get_chatgpt_meal_suggestion_network_error(self, mock_post):
        """ネットワークエラーが発生した場合、OpenAIErrorが発生すること"""
        mock_post.side_effect = Exception("Network error")

        adapter = OpenAIAdapter()
        with pytest.raises(OpenAIError) as excinfo:
            adapter.get_chatgpt_meal_suggestion()

        assert "Network error" in str(excinfo.value)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test_api_key"}, clear=True)
    @patch("requests.post")
    def test_get_chatgpt_response_network_error(self, mock_post):
        """ネットワークエラーが発生した場合、OpenAIErrorが発生すること"""
        mock_post.side_effect = Exception("Connection timeout")

        adapter = OpenAIAdapter()
        with pytest.raises(OpenAIError) as excinfo:
            adapter.get_chatgpt_response("テスト")

        assert "Connection timeout" in str(excinfo.value)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test_api_key"}, clear=True)
    @patch("requests.post")
    def test_get_chatgpt_response_strips_whitespace(self, mock_post):
        """応答の前後の空白が除去されること"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "  こんにちは！  \n"}}]
        }
        mock_post.return_value = mock_response

        adapter = OpenAIAdapter()
        result = adapter.get_chatgpt_response("テスト")

        assert result == "こんにちは！"

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test_api_key"}, clear=True)
    @patch("requests.post")
    def test_error_response_body_truncation(self, mock_post):
        """エラーレスポンスのボディが長い場合、切り詰められること"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "x" * 3000  # 3000文字の長いエラーメッセージ
        mock_post.return_value = mock_response

        adapter = OpenAIAdapter()
        with pytest.raises(OpenAIError) as excinfo:
            adapter.get_chatgpt_meal_suggestion()

        error_message = str(excinfo.value)
        assert "[truncated]" in error_message
        assert len(error_message) < 2500  # 切り詰められている

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test_api_key"}, clear=True)
    @patch("requests.post")
    def test_authorization_header_is_set(self, mock_post):
        """Authorizationヘッダーが正しく設定されること"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "テスト応答"}}]
        }
        mock_post.return_value = mock_response

        adapter = OpenAIAdapter()
        adapter.get_chatgpt_response("テスト")

        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer test_api_key"
        assert headers["Content-Type"] == "application/json"

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test_api_key"}, clear=True)
    @patch("requests.post")
    def test_timeout_is_set(self, mock_post):
        """タイムアウトが設定されていること"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "テスト応答"}}]
        }
        mock_post.return_value = mock_response

        adapter = OpenAIAdapter()
        adapter.get_chatgpt_response("テスト")

        call_args = mock_post.call_args
        assert call_args[1]["timeout"] == 30

    @patch.dict(
        "os.environ",
        {
            "OPENAI_API_KEY": "test_api_key",
            "PROMPTLAYER_API_KEY": "test_promptlayer_key",
        },
        clear=True,
    )
    @patch("src.infrastructure.adapters.openai_adapter.promptlayer_available", True)
    @patch("src.infrastructure.adapters.openai_adapter.promptlayer")
    def test_get_chatgpt_response_with_promptlayer(self, mock_promptlayer):
        """PromptLayer SDKを使用してチャット応答を取得できること"""
        # PromptLayerのOpenAIクライアントをモック
        mock_openai_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "PromptLayerで応答！"
        mock_openai_client.chat.completions.create.return_value = mock_response
        mock_promptlayer.openai.OpenAI.return_value = mock_openai_client

        adapter = OpenAIAdapter()
        result = adapter.get_chatgpt_response("こんにちは")

        assert result == "PromptLayerで応答！"
        assert adapter.use_promptlayer is True

        # PromptLayer SDKのcreateメソッドが呼ばれたことを確認
        mock_openai_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
        assert call_kwargs["pl_tags"] == ["chat_response"]

    @patch.dict(
        "os.environ",
        {
            "OPENAI_API_KEY": "test_api_key",
            "PROMPTLAYER_API_KEY": "test_promptlayer_key",
        },
        clear=True,
    )
    @patch("src.infrastructure.adapters.openai_adapter.promptlayer_available", True)
    @patch("src.infrastructure.adapters.openai_adapter.promptlayer")
    def test_promptlayer_sdk_failure_falls_back_to_direct_api(self, mock_promptlayer):
        """PromptLayer SDKの初期化が失敗した場合、直接APIにフォールバックすること"""
        # PromptLayer SDKの初期化で例外を発生させる
        mock_promptlayer.openai.OpenAI.side_effect = Exception(
            "PromptLayer init failed"
        )

        adapter = OpenAIAdapter()

        # PromptLayerの初期化に失敗したのでFalseになる
        assert adapter.use_promptlayer is False
        assert adapter.openai_client is None
