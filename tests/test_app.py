import types
from src.infrastructure.line_model import create_pokemon_zukan_flex_dict

class DummyFlex:
    def __init__(self, alt_text, contents):
        self.alt_text = alt_text
        self.contents = contents

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
