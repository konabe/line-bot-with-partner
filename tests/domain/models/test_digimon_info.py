"""DigimonInfo ドメインモデルのテスト"""

from src.domain.models.digimon_info import DigimonInfo


class TestDigimonInfo:
    def test_from_mapping_with_valid_data(self):
        """正常なデータからDigimonInfoを生成できること"""
        data = {
            "id": 1,
            "name": "Agumon",
            "level": "Rookie",
            "images": [{"href": "https://example.com/agumon.png"}],
        }

        info = DigimonInfo.from_mapping(data)

        assert info.id == 1
        assert info.name == "Agumon"
        assert info.level == "Rookie"
        assert info.image_url == "https://example.com/agumon.png"

    def test_from_mapping_with_empty_data(self):
        """空のデータでもエラーにならず、デフォルト値が設定されること"""
        data = {}

        info = DigimonInfo.from_mapping(data)

        assert info.id == 0
        assert info.name == ""
        assert info.level == ""
        assert info.image_url is None

    def test_from_mapping_with_none(self):
        """Noneを渡してもエラーにならないこと"""
        info = DigimonInfo.from_mapping(None)

        assert info.id == 0
        assert info.name == ""
        assert info.level == ""
        assert info.image_url is None

    def test_from_mapping_without_images(self):
        """imagesキーがない場合、image_urlがNoneになること"""
        data = {"id": 2, "name": "Gabumon", "level": "Rookie"}

        info = DigimonInfo.from_mapping(data)

        assert info.id == 2
        assert info.name == "Gabumon"
        assert info.level == "Rookie"
        assert info.image_url is None

    def test_from_mapping_with_empty_images(self):
        """imagesが空リストの場合、image_urlがNoneになること"""
        data = {"id": 3, "name": "Patamon", "level": "Rookie", "images": []}

        info = DigimonInfo.from_mapping(data)

        assert info.image_url is None
