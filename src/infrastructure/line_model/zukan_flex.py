from linebot.v3.messaging import models

def create_pokemon_zukan_button_template(info):
    type_text = ' / '.join(info.get('types') or []) if info.get('types') else '不明'
    image_url = info.get('image_url') or "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/0.png"
    zukan_no = info.get('zukan_no') or 0
    # zero-pad to 4 digits, e.g. 25 -> '0025'
    try:
        zukan_id_str = f"{int(zukan_no):04d}"
    except Exception:
        zukan_id_str = str(zukan_no)

    title = f"No.{zukan_no} {info.get('name')}"

    detail_url = f"https://zukan.pokemon.co.jp/detail/{zukan_id_str}"

    template = models.ButtonsTemplate(
        title=title,
        text=f"タイプ: {type_text}",
        thumbnail_image_url=image_url,
        actions=[models.URIAction(label='図鑑で見る', uri=detail_url)],
    )
    return models.TemplateMessage(alt_text='ポケモン図鑑', template=template)
