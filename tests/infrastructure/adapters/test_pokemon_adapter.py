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


def test_translate_types_to_japanese():
    """英語タイプの日本語変換テスト"""
    # 基本的なタイプ変換
    result = PokemonInfo.translate_types_to_japanese(["fire", "water"])
    assert result == ["ほのお", "みず"]

    # 単一タイプ
    result = PokemonInfo.translate_types_to_japanese(["electric"])
    assert result == ["でんき"]

    # 未知のタイプは元のまま
    result = PokemonInfo.translate_types_to_japanese(["unknown_type"])
    assert result == ["unknown_type"]

    # 空のリスト
    result = PokemonInfo.translate_types_to_japanese([])
    assert result == []

    # 複数タイプ（ドラゴン/ひこう）
    result = PokemonInfo.translate_types_to_japanese(["dragon", "flying"])
    assert result == ["ドラゴン", "ひこう"]


# 注意: 実際のAPIを呼び出すテストは、モックやフィクスチャーが必要
# 本番では外部API依存を避けるためにモックを使用すること
