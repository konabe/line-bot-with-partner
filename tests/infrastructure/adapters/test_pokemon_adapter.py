from src.domain.models.pokemon_info import PokemonInfo
from src.infrastructure.adapters.pokemon_adapter import PokemonApiAdapter


def test_pokemon_adapter_get_japanese_name():
    """日本語名取得のテスト"""
    adapter = PokemonApiAdapter()

    # フォールバック名のテスト
    result = adapter._get_japanese_name({}, "pikachu")
    assert result == "pikachu"


def test_pokemon_adapter_initialization():
    """アダプター初期化のテスト"""
    adapter = PokemonApiAdapter()
    assert adapter.logger is not None


def test_types_ja_property():
    """types_jaプロパティのテスト"""
    # 基本的なタイプ変換
    info = PokemonInfo(name="Test", types=["fire", "water"], image_url=None, zukan_no=1)
    assert info.types_ja == ["ほのお", "みず"]

    # 単一タイプ
    info = PokemonInfo(name="Test", types=["electric"], image_url=None, zukan_no=1)
    assert info.types_ja == ["でんき"]

    # 未知のタイプは元のまま
    info = PokemonInfo(name="Test", types=["unknown_type"], image_url=None, zukan_no=1)
    assert info.types_ja == ["unknown_type"]

    # 空のリスト
    info = PokemonInfo(name="Test", types=[], image_url=None, zukan_no=1)
    assert info.types_ja == []

    # 複数タイプ（ドラゴン/ひこう）
    info = PokemonInfo(
        name="Test", types=["dragon", "flying"], image_url=None, zukan_no=1
    )
    assert info.types_ja == ["ドラゴン", "ひこう"]


# 注意: 実際のAPIを呼び出すテストは、モックやフィクスチャーが必要
# 本番では外部API依存を避けるためにモックを使用すること
