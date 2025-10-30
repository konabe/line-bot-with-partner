"""デジモン図鑑ButtonTemplateのテスト"""

from src.domain.models.digimon_info import DigimonInfo
from src.infrastructure.line_model.digimon_button_template import (
    create_digimon_zukan_button_template,
)


class TestCreateDigimonZukanButtonTemplate:
    def test_create_template_with_valid_info(self):
        """正常なデジモン情報でButtonTemplateを作成できること"""
        info = DigimonInfo(
            id=1,
            name="Agumon",
            level="Rookie",
            image_url="https://example.com/agumon.png",
        )

        result = create_digimon_zukan_button_template(info)

        assert result.__class__.__name__ == "TemplateMessage"
        assert result.alt_text == "デジモン図鑑"

        template = result.template
        assert template.__class__.__name__ == "ButtonsTemplate"
        assert "No.0001" in template.title
        assert "Agumon" in template.title
        assert "レベル: Rookie" in template.text
        assert template.thumbnail_image_url == "https://example.com/agumon.png"
        assert len(template.actions) == 1
        assert template.actions[0].label == "図鑑で見る"
        assert "https://digi-api.com/digimon/1" in template.actions[0].uri

    def test_create_template_with_none_image_url(self):
        """image_urlがNoneの場合にデフォルト画像が使用されること"""
        info = DigimonInfo(id=2, name="Gabumon", level="Rookie", image_url=None)

        result = create_digimon_zukan_button_template(info)

        template = result.template
        assert (
            template.thumbnail_image_url
            == "https://digi-api.com/images/digimon/w/Agumon.png"
        )

    def test_create_template_with_empty_level(self):
        """レベルが空の場合に「不明」が表示されること"""
        info = DigimonInfo(
            id=3,
            name="Patamon",
            level="",
            image_url="https://example.com/patamon.png",
        )

        result = create_digimon_zukan_button_template(info)

        template = result.template
        assert "レベル: 不明" in template.text

    def test_create_template_with_large_id(self):
        """大きなIDでも正しくフォーマットされること"""
        info = DigimonInfo(
            id=1422,
            name="Renamon",
            level="Rookie",
            image_url="https://example.com/renamon.png",
        )

        result = create_digimon_zukan_button_template(info)

        template = result.template
        assert "No.1422" in template.title

    def test_create_template_with_mapping(self):
        """Mappingから作成できること"""
        data = {
            "id": 10,
            "name": "Tentomon",
            "level": "Rookie",
            "images": [{"href": "https://example.com/tentomon.png"}],
        }

        result = create_digimon_zukan_button_template(data)

        assert result.__class__.__name__ == "TemplateMessage"
        template = result.template
        assert "No.0010" in template.title
        assert "Tentomon" in template.title
