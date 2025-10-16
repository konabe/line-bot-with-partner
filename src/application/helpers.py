import logging
import requests
import random
from linebot.v3.messaging.models import FlexBubble, FlexImage, FlexBox, FlexText

logger = logging.getLogger(__name__)


def get_random_pokemon_info():
    """ランダムなポケモン情報を取得します（レガシー関数、互換性のために保持）。"""
    try:
        logger.debug("get_random_pokemon_info called")
        resp = requests.get('https://pokeapi.co/api/v2/pokemon?limit=1')
        resp.raise_for_status()
        count = resp.json().get('count', 1000)
        poke_id = random.randint(1, count)
        resp2 = requests.get(f'https://pokeapi.co/api/v2/pokemon/{poke_id}')
        resp2.raise_for_status()
        name = resp2.json().get('name', '不明')
        image_url = resp2.json().get('sprites', {}).get('other', {}).get('official-artwork', {}).get('front_default')
        species_url = resp2.json().get('species', {}).get('url')
        if species_url:
            resp3 = requests.get(species_url)
            resp3.raise_for_status()
            names = resp3.json().get('names', [])
            for n in names:
                if n.get('language', {}).get('name') == 'ja':
                    name = n.get('name')
                    break
        logger.info(f"取得したポケモン: {name}")
        return {'name': name, 'image_url': image_url}
    except Exception as e:
        logger.error(f"get_random_pokemon_info error: {e}")
        return None


def create_pokemon_flex(name, image_url):
    """シンプルなポケモン Flex メッセージを作成します（レガシー関数、互換性のために保持）。"""
    hero = FlexImage(url=image_url or "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/0.png", size="xl", aspect_ratio="1:1", aspect_mode="cover")
    body = FlexBox(layout="vertical", contents=[
        FlexText(text=name, weight="bold", size="xl", align="center")
    ])
    bubble = FlexBubble(hero=hero, body=body)
    from linebot.v3.messaging.models import FlexMessage
    return FlexMessage(alt_text=f"今日のポケモン: {name}", contents=bubble)