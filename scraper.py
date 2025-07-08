# scraper.py
import requests
import json
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}


def build_translation_maps(filters_data):
    """
    Создает мастер-словари для перевода ID в текст.
    Пример: {'amenities': {'1': 'Мебель', '2': 'Холодильник'}, 'type': {'sell': 'Покупка'}}
    """
    master_map = {}
    for filter_item in filters_data:
        technical_name = filter_item.get('name')
        values = filter_item.get('values')
        if not technical_name or not values:
            continue

        translation_map = {}
        for option in values:
            option_id = option.get('value')
            option_label = option.get('labels', {}).get('ru')
            if option_id is not None and option_label is not None:
                translation_map[str(option_id)] = option_label

        master_map[technical_name] = translation_map
    return master_map


def get_page_data(url):
    """
    Функция для получения всех данных, включая динамически созданные словари-переводчики.
    """
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"error": f"Ошибка сети: {e}"}

    soup = BeautifulSoup(response.text, 'html.parser')
    script_tag = soup.find('script', id='__NEXT_DATA__')
    if not script_tag:
        return {"error": "Не удалось найти данные на странице (тег __NEXT_DATA__)."}

    try:
        data = json.loads(script_tag.string)

        listing_data = data['props']['initialState']['listing']
        filters_data = data['props']['initialState'].get(
            'filters', {}).get('pageFilters', [])

        regular_ads = listing_data.get('ads', [])
        vip_ads = listing_data.get('vip', [])
        all_apartments = vip_ads + regular_ads

        pagination_list = listing_data.get('pagination', [])
        next_page_token = next(
            (p.get('token') for p in pagination_list if p.get('label') == 'next'), None)

        translation_maps = build_translation_maps(filters_data)

        return {
            "apartments": all_apartments,
            "next_page_token": next_page_token,
            "total_ads": int(listing_data.get('total', 0)),
            "translation_maps": translation_maps
        }
    except (KeyError, json.JSONDecodeError) as e:
        return {"error": f"Ошибка обработки структуры данных: {e}"}
