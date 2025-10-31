"""OpenAIAdapter のテスト (OpenAI SDK版)"""

from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.adapters.openai_adapter import OpenAIAdapter, OpenAIError


class TestOpenAIAdapter:
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test_api_key"}, clear=True)
    @patch("src.infrastructure.adapters.openai_adapter.OpenAI")
    def test_init_with_api_key(self, mock_openai_class):
        """環境変数にAPI Keyがある場合、正常に初期化できること"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        adapter = OpenAIAdapter()

        assert adapter.api_key == "test_api_key"
        assert adapter.model == "gpt-5-mini"
        assert adapter.use_promptlayer is False
        assert adapter.openai_client is mock_client

    @patch.dict(
        "os.environ",
        {"OPENAI_API_KEY": "test_api_key", "OPENAI_MODEL": "gpt-4"},
        clear=True,
    )
    @patch("src.infrastructure.adapters.openai_adapter.OpenAI")
    def test_init_with_custom_model(self, mock_openai_class):
        """カスタムモデルを指定できること"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        adapter = OpenAIAdapter()

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
    @patch("src.infrastructure.adapters.openai_adapter.OpenAI")
    def test_init_with_promptlayer(self, mock_openai_class, mock_promptlayer):
        """PROMPTLAYER_API_KEYがある場合、PromptLayerが有効になること"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_pl_client = MagicMock()
        mock_promptlayer.PromptLayer.return_value = mock_pl_client

        adapter = OpenAIAdapter()

        assert adapter.use_promptlayer is True
        assert adapter.promptlayer_client is mock_pl_client

    @patch.dict("os.environ", {}, clear=True)
    def test_init_without_api_key(self):
        """環境変数にAPI Keyがない場合、エラーが発生すること"""
        with pytest.raises(OpenAIError) as excinfo:
            OpenAIAdapter()

        assert "OPENAI_API_KEY is not set" in str(excinfo.value)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test_api_key"}, clear=True)
    @patch("src.infrastructure.adapters.openai_adapter.OpenAI")
    def test_get_chatgpt_meal_suggestion_success(self, mock_openai_class):
        """料理提案を正常に取得できること"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "カレーライス"
        mock_client.chat.completions.create.return_value = mock_response

        adapter = OpenAIAdapter()
        result = adapter.get_chatgpt_meal_suggestion()

        assert "カレーライス" in result
        mock_client.chat.completions.create.assert_called_once()

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test_api_key"}, clear=True)
    @patch("src.infrastructure.adapters.openai_adapter.OpenAI")
    def test_get_chatgpt_response_success(self, mock_openai_class):
        """チャット応答を正常に取得できること"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "こんにちは！"
        mock_client.chat.completions.create.return_value = mock_response

        adapter = OpenAIAdapter()
        result = adapter.get_chatgpt_response("こんにちは")

        assert result == "こんにちは！"

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test_api_key"}, clear=True)
    @patch("src.infrastructure.adapters.openai_adapter.OpenAI")
    def test_api_error(self, mock_openai_class):
        """APIがエラーを返した場合、OpenAIErrorが発生すること"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        adapter = OpenAIAdapter()
        with pytest.raises(OpenAIError):
            adapter.get_chatgpt_response("テスト")

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test_api_key"}, clear=True)
    @patch("src.infrastructure.adapters.openai_adapter.OpenAI")
    def test_empty_content(self, mock_openai_class):
        """contentが空の場合、エラーが発生すること"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_client.chat.completions.create.return_value = mock_response

        adapter = OpenAIAdapter()
        with pytest.raises(OpenAIError):
            adapter.get_chatgpt_response("テスト")

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
    @patch("src.infrastructure.adapters.openai_adapter.OpenAI")
    @patch("requests.post")
    def test_promptlayer_logging(
        self, mock_requests_post, mock_openai_class, mock_promptlayer
    ):
        """PromptLayerへのログ送信が正常に動作すること"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_pl_client = MagicMock()
        mock_promptlayer.PromptLayer.return_value = mock_pl_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "テスト応答"
        mock_response.model_dump.return_value = {"id": "test-id"}
        mock_client.chat.completions.create.return_value = mock_response

        mock_pl_response = MagicMock()
        mock_pl_response.status_code = 200
        mock_requests_post.return_value = mock_pl_response

        adapter = OpenAIAdapter()
        result = adapter.get_chatgpt_response("こんにちは")

        assert result == "テスト応答"
        mock_requests_post.assert_called_once()
        pl_payload = mock_requests_post.call_args[1]["json"]
        assert pl_payload["api_key"] == "test_promptlayer_key"
