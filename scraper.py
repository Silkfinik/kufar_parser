# scraper.py
import requests
import json
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}


def get_page_data(url):
    """
    Функция для получения всех данных (объявления, пагинация, общее кол-во) с одной страницы.
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

        regular_ads = listing_data.get('ads', [])
        vip_ads = listing_data.get('vip', [])
        all_apartments = vip_ads + regular_ads

        pagination_list = listing_data.get('pagination', [])
        next_page_token = None
        for page_info in pagination_list:
            if page_info.get('label') == 'next':
                next_page_token = page_info.get('token')
                break

        return {
            "apartments": all_apartments,
            "next_page_token": next_page_token,
            "total_ads": int(listing_data.get('total', 0))
        }
    except (KeyError, json.JSONDecodeError) as e:
        return {"error": f"Ошибка обработки структуры данных: {e}"}
