from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class PokemonInfo:
    """Value object representing the minimal data needed for the
    pokemon zukan templates.

    This is intentionally small and immutable. Callers can construct it
    directly or use the `from_mapping` helper to convert a dict-like
    payload (for backward compatibility).
    """

    name: str
    types: List[str]
    image_url: Optional[str]
    zukan_no: int

    @classmethod
    def from_mapping(cls, data: Dict[str, Any]) -> "PokemonInfo":
        """Create a PokemonInfo from a mapping/dict-like object.

        The input is tolerant: missing values are converted to sensible
        defaults (empty name, empty types, 0 zukan_no).
        """
        if data is None:
            data = {}
        name = data.get("name") or ""
        types_raw = data.get("types") or []
        # Ensure list of strings
        types = [str(t) for t in types_raw] if types_raw else []
        image_url = data.get("image_url")
        zukan_no_raw = data.get("zukan_no")
        try:
            zukan_no = int(zukan_no_raw) if zukan_no_raw not in (None, "") else 0
        except Exception:
            # Fallback to 0 if conversion fails
            zukan_no = 0

        return cls(name=name, types=types, image_url=image_url, zukan_no=zukan_no)


__all__ = ["PokemonInfo"]
