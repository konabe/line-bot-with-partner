"""DigimonApiAdapter のテスト"""

from unittest.mock import MagicMock, patch

from src.domain.models.digimon_info import DigimonInfo
from src.infrastructure.adapters.digimon_adapter import DigimonApiAdapter


class TestDigimonApiAdapter:
    @patch("src.infrastructure.adapters.digimon_adapter.requests.get")
    @patch("src.infrastructure.adapters.digimon_adapter.random.randint")
    def test_get_random_digimon_info_success(self, mock_randint, mock_get):
        """正常にデジモン情報を取得できること"""
        mock_randint.return_value = 1
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 1,
            "name": "Agumon",
            "level": "Rookie",
            "images": [{"href": "https://example.com/agumon.png"}],
        }
        mock_get.return_value = mock_response

        adapter = DigimonApiAdapter()
        info = adapter.get_random_digimon_info()

        assert isinstance(info, DigimonInfo)
        assert info.id == 1
        assert info.name == "Agumon"
        assert info.level == "Rookie"
        assert info.image_url == "https://example.com/agumon.png"

        mock_get.assert_called_once_with(
            "https://digi-api.com/api/v1/digimon/1", timeout=10
        )

    @patch("src.infrastructure.adapters.digimon_adapter.requests.get")
    @patch("src.infrastructure.adapters.digimon_adapter.random.randint")
    def test_get_random_digimon_info_request_error(self, mock_randint, mock_get):
        """APIリクエストエラー時にNoneを返すこと"""
        mock_randint.return_value = 1
        mock_get.side_effect = Exception("Network error")

        adapter = DigimonApiAdapter()
        info = adapter.get_random_digimon_info()

        assert info is None

    @patch("src.infrastructure.adapters.digimon_adapter.requests.get")
    @patch("src.infrastructure.adapters.digimon_adapter.random.randint")
    def test_get_random_digimon_info_json_error(self, mock_randint, mock_get):
        """JSON解析エラー時にNoneを返すこと"""
        mock_randint.return_value = 1
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        adapter = DigimonApiAdapter()
        info = adapter.get_random_digimon_info()

        assert info is None
