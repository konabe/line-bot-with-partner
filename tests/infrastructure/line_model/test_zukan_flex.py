from src.infrastructure.line_model import create_pokemon_zukan_flex_dict

def test_create_pokemon_zukan_flex_dict():
    info = {
        'zukan_no': 25,
        'name': 'ピカチュウ',
        'image_url': 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png',
        'types': ['electric'],
        'evolution': 'pichu → pikachu → raichu'
    }
    flex = create_pokemon_zukan_flex_dict(info)
    assert flex['hero']['url'] == info['image_url']
    assert f"No.{info['zukan_no']} {info['name']}" in str(flex)
    assert 'タイプ: electric' in str(flex)
