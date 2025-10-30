"""Pokemon API アダプターのテスト"""

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


# 注意: 実際のAPIを呼び出すテストは、モックやフィクスチャーが必要
# 本番では外部API依存を避けるためにモックを使用すること
