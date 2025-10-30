from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class DigimonInfo:
    id: int
    name: str
    level: str
    image_url: Optional[str]

    @classmethod
    def from_mapping(cls, data: Dict[str, Any]) -> "DigimonInfo":
        if data is None:
            data = {}
        digimon_id = data.get("id", 0)
        try:
            digimon_id = int(digimon_id) if digimon_id not in (None, "") else 0
        except Exception:
            digimon_id = 0

        name = data.get("name") or ""
        level = data.get("level") or ""

        images = data.get("images") or []
        image_url = None
        if images and len(images) > 0:
            image_url = images[0].get("href")

        return cls(id=digimon_id, name=name, level=level, image_url=image_url)


__all__ = ["DigimonInfo"]
