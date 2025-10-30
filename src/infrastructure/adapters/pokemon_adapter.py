"""Pokemon API との通信を行うアダプター"""

import random
from typing import Optional

import requests

from ...domain.models.pokemon_info import PokemonInfo
from ..logger import Logger, create_logger


class PokemonApiAdapter:
    """Pokemon API からポケモン情報を取得するアダプター"""

    def __init__(self, logger: Optional[Logger] = None):
        self.logger: Logger = logger or create_logger(__name__)

    def get_random_pokemon_info(self) -> Optional[PokemonInfo]:
        """ランダムなポケモンの図鑑情報を取得します"""
        try:
            # ランダムなポケモンを取得（1-1000の範囲）
            poke_id = random.randint(1, 1000)
            self.logger.debug(f"Fetching Pokemon ID: {poke_id}")

            resp = requests.get(
                f"https://pokeapi.co/api/v2/pokemon/{poke_id}", timeout=10
            )
            resp.raise_for_status()
            data = resp.json()

            # 基本情報
            zukan_no = data["id"]
            name_en = data["name"]

            # 日本語名を取得
            name = self._get_japanese_name(data, name_en)

            # タイプ
            types = [t["type"]["name"] for t in data.get("types", [])]

            # 画像URL
            image_url = (
                data.get("sprites", {})
                .get("other", {})
                .get("official-artwork", {})
                .get("front_default")
            )

            return PokemonInfo(
                zukan_no=zukan_no, name=name, types=types, image_url=image_url
            )

        except Exception as e:
            self.logger.error(f"ポケモン情報取得エラー: {e}")
            return None

    def _get_japanese_name(self, pokemon_data: dict, fallback_name: str) -> str:
        """ポケモンの日本語名を取得する（失敗時は英語名を返す）"""
        species_url = pokemon_data.get("species", {}).get("url")
        if not species_url:
            return fallback_name

        try:
            species_resp = requests.get(species_url, timeout=10)
            species_resp.raise_for_status()
            species_data = species_resp.json()

            for name_info in species_data.get("names", []):
                if name_info.get("language", {}).get("name") == "ja":
                    return name_info.get("name", fallback_name)

        except Exception as e:
            self.logger.warning(f"日本語名取得に失敗: {e}")

        return fallback_name
