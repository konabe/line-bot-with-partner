from typing import Mapping, Union
from linebot.v3.messaging.models import TemplateMessage, ButtonsTemplate, URIAction
from src.domain.models.pokemon_info import PokemonInfo


def create_pokemon_zukan_button_template(info: Union[PokemonInfo, Mapping]):
    """Create a ButtonsTemplate-based TemplateMessage for a Pokemon.

    Args:
        info: either a `PokemonInfo` instance or a mapping (dict-like). If a
            mapping is provided it will be converted with
            `PokemonInfo.from_mapping` for backward compatibility.
    """
    if not isinstance(info, PokemonInfo):
        info = PokemonInfo.from_mapping(dict(info or {}))

    types = info.types or []
    type_text = " / ".join(types) if types else "不明"
    image_url = (
        info.image_url
        or "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/0.png"
    )
    zukan_no = info.zukan_no or 0

    # zero-pad to 4 digits, e.g. 25 -> '0025'
    try:
        zukan_id_str = f"{int(zukan_no):04d}"
    except Exception:
        zukan_id_str = str(zukan_no)

    title = f"No.{zukan_id_str} {info.name or ''}".strip()

    detail_url = f"https://zukan.pokemon.co.jp/detail/{zukan_id_str}"

    # Build SDK model instances directly using the correct parameter names
    # (camelCase) expected by the installed SDK.
    actions = [URIAction(label="図鑑で見る", uri=detail_url, altUri=None)]

    template = ButtonsTemplate(
        title=title,
        text=f"タイプ: {type_text}",
        thumbnailImageUrl=image_url,
        actions=actions,
        imageAspectRatio="rectangle",
        imageSize="cover",
        imageBackgroundColor="#FFFFFF",
        defaultAction=None,
    )

    return TemplateMessage(altText="ポケモン図鑑", template=template, quickReply=None)
