"""Digimon API との通信を行うアダプター"""

import random
from typing import Optional

import requests

from ...domain.models.digimon_info import DigimonInfo
from ..logger import Logger


class DigimonApiAdapter:
    def __init__(self, logger: Logger):
        self.logger = logger

    def get_random_digimon_info(self) -> Optional[DigimonInfo]:
        try:
            digimon_id = random.randint(1, 1422)
            self.logger.debug(f"Fetching Digimon ID: {digimon_id}")

            resp = requests.get(
                f"https://digi-api.com/api/v1/digimon/{digimon_id}", timeout=10
            )
            resp.raise_for_status()
            data = resp.json()

            return DigimonInfo.from_mapping(data)

        except requests.RequestException as e:
            self.logger.error(f"デジモンAPI通信エラー: {e}")
            return None
        except Exception as e:
            self.logger.error(f"デジモン情報取得エラー: {e}")
            return None
