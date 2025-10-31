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
        assert adapter.promptlayer_api_key is None
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
    @patch("src.infrastructure.adapters.openai_adapter.PromptLayer")
    def test_init_with_promptlayer(self, mock_promptlayer_class):
        """PROMPTLAYER_API_KEYがある場合、PromptLayerが有効になること"""
        mock_pl_client = MagicMock()
        mock_wrapped_openai = MagicMock()
        mock_pl_client.openai.OpenAI.return_value = mock_wrapped_openai
        mock_promptlayer_class.return_value = mock_pl_client

        adapter = OpenAIAdapter()

        assert adapter.promptlayer_api_key == "test_promptlayer_key"
        assert adapter.openai_client is mock_wrapped_openai
        mock_promptlayer_class.assert_called_once_with(api_key="test_promptlayer_key")

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
    @patch("src.infrastructure.adapters.openai_adapter.PromptLayer")
    def test_promptlayer_logging(self, mock_promptlayer_class):
        """PromptLayerへのログ送信が正常に動作すること"""
        mock_pl_client = MagicMock()
        mock_wrapped_openai = MagicMock()
        mock_pl_client.openai.OpenAI.return_value = mock_wrapped_openai
        mock_promptlayer_class.return_value = mock_pl_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "テスト応答"
        mock_wrapped_openai.chat.completions.create.return_value = mock_response

        adapter = OpenAIAdapter()
        result = adapter.get_chatgpt_response("こんにちは")

        assert result == "テスト応答"
        # PromptLayerでラップされたクライアントが呼ばれたことを確認
        mock_wrapped_openai.chat.completions.create.assert_called_once()
        call_kwargs = mock_wrapped_openai.chat.completions.create.call_args[1]
        assert "pl_tags" in call_kwargs
        assert call_kwargs["pl_tags"] == ["chat_response"]
