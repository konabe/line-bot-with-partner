import dataclasses
from typing import Any, cast

import pytest

from src.domain.models.pokemon_info import PokemonInfo


def test_from_mapping_none_returns_defaults():
    info = PokemonInfo.from_mapping(cast(Any, None))
    assert info.name == ""
    assert info.types == []
    assert info.image_url is None
    assert info.zukan_no == 0


def test_from_mapping_with_full_data():
    data = {
        "name": "Pikachu",
        "types": ["Electric"],
        "image_url": "https://example.com/pikachu.png",
        "zukan_no": 25,
    }
    info = PokemonInfo.from_mapping(data)
    assert info.name == "Pikachu"
    assert info.types == ["Electric"]
    assert info.image_url == "https://example.com/pikachu.png"
    assert info.zukan_no == 25


def test_from_mapping_types_are_stringified():
    # numeric types should be converted to strings
    data = {"types": [1, "Water"]}
    info = PokemonInfo.from_mapping(data)
    assert info.types == ["1", "Water"]


def test_from_mapping_zukan_no_string_and_invalid():
    info1 = PokemonInfo.from_mapping({"zukan_no": "7"})
    assert info1.zukan_no == 7

    info2 = PokemonInfo.from_mapping({"zukan_no": "not-a-number"})
    assert info2.zukan_no == 0


def test_dataclass_is_frozen():
    info = PokemonInfo.from_mapping({"name": "Bulbasaur"})
    # assignment should raise FrozenInstanceError (or AttributeError on some runtimes)
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        info.name = "Ivysaur"  # type: ignore
