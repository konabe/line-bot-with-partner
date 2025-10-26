"""ポケモン図鑑FLEX Message生成ユーティリティ

このモジュールは2つのヘルパーを提供します:
- create_pokemon_zukan_flex_dict(info): LINE API の bubble dict を返す (既存の互換関数)
- create_pokemon_zukan_flex_model(info): SDK の Pydantic モデル (FlexMessage 等) を返す。SDK が利用できない場
    合は dict を返します。
"""


def create_pokemon_zukan_flex_dict(info):
    type_text = ' / '.join(info['types']) if info['types'] else '不明'
    flex = {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": info['image_url'] or "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/0.png",
            "size": "xl",
            "aspectRatio": "1:1",
            "aspectMode": "cover"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"No.{info['zukan_no']} {info['name']}",
                    "weight": "bold",
                    "size": "xl",
                    "align": "center"
                },
                {
                    "type": "text",
                    "text": f"タイプ: {type_text}",
                    "size": "md",
                    "align": "center"
                },
                {
                    "type": "text",
                    "text": f"進化: {info['evolution']}",
                    "size": "sm",
                    "align": "center"
                }
            ]
        }
    }
    return flex


def create_pokemon_zukan_flex_model(info):
    """SDK の FlexMessage モデルを組み立てて返す。SDK が利用できない場合は dict を返す。

    Args:
        info: dict (zukan_no, name, image_url, types, evolution)
    Returns:
        FlexMessage instance (linebot.v3.messaging.models.FlexMessage) or dict (bubble contents)
    """
    try:
        from linebot.v3.messaging import models

        type_text = ' / '.join(info['types']) if info.get('types') else '不明'

        hero = models.FlexImage(url=info.get('image_url') or "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/0.png", size='xl', aspectRatio='1:1', aspectMode='cover')

        body_contents = [
            models.FlexText(text=f"No.{info['zukan_no']} {info['name']}", weight='bold', size='xl', align='center'),
            models.FlexText(text=f"タイプ: {type_text}", size='md', align='center'),
            models.FlexText(text=f"進化: {info.get('evolution')}", size='sm', align='center'),
        ]

        body = models.FlexBox(layout='vertical', contents=body_contents)

        bubble = models.FlexBubble(hero=hero, body=body)

        flex_message = models.FlexMessage(altText='ポケモン図鑑', contents=bubble)
        return flex_message
    except Exception:
        # SDK が無い、またはモデル生成に失敗した場合は互換 dict を返す
        return create_pokemon_zukan_flex_dict(info)
