import math  # Добавляем импорт для математических операций
import requests
import json
from bs4 import BeautifulSoup
import time
import math

# --- НАСТРОЙКИ ---
# Базовый URL для поиска. Позже мы научимся добавлять сюда фильтры.
BASE_URL = "https://re.kufar.by/l/minsk/snyat/kvartiru"
# Сколько максимум страниц мы хотим обойти
MAX_PAGES_TO_SCRAPE = 3
# Задержка между запросами, чтобы не нагружать сайт
SLEEP_DELAY_SECONDS = 2

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}


def get_page_data(url):
    """
    Функция для получения всех данных (объявления и пагинация) с одной страницы.
    """
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при запросе страницы {url}: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    script_tag = soup.find('script', id='__NEXT_DATA__')
    if not script_tag:
        return None

    try:
        data = json.loads(script_tag.string)
        listing_data = data['props']['initialState']['listing']

        regular_ads = listing_data.get('ads', [])
        vip_ads = listing_data.get('vip', [])
        all_apartments = vip_ads + regular_ads

        # Находим токен для следующей страницы
        pagination_list = listing_data.get('pagination', [])
        next_page_token = None
        for page_info in pagination_list:
            if page_info.get('label') == 'next':
                next_page_token = page_info.get('token')
                break

        return {
            "apartments": all_apartments,
            "next_page_token": next_page_token
        }
    except (KeyError, json.JSONDecodeError) as e:
        print(f"❌ Ошибка обработки данных: {e}")
        return None


# --- ГЛАВНАЯ ЛОГИКА ---
if __name__ == "__main__":
    all_found_apartments = []
    current_url = BASE_URL

    # --- ШАГ 1: Узнаем, сколько всего страниц нужно обойти ---
    print(" sonde Сначала определим общее количество объявлений...")
    first_page_data = get_page_data(current_url)

    if not first_page_data:
        exit("❌ Не удалось загрузить первую страницу. Невозможно рассчитать количество страниц.")

    try:
        response = requests.get(current_url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', id='__NEXT_DATA__')
        full_data = json.loads(script_tag.string)

        # ИСПРАВЛЕНИЕ: Преобразуем total в число с помощью int()
        total_ads = int(full_data['props']
                        ['initialState']['listing'].get('total', 0))

        ads_on_first_page = len(first_page_data.get('apartments', []))

        if total_ads > 0 and ads_on_first_page > 0:
            max_pages = math.ceil(total_ads / ads_on_first_page)
            print(
                f"📊 Всего найдено {total_ads} объявлений. Это примерно {max_pages} страниц.")
        else:
            max_pages = 1

    except Exception as e:
        print(
            f"❌ Не удалось автоматически определить количество страниц: {e}. Устанавливаю лимит в 1 страницу.")
        max_pages = 1

    all_found_apartments.extend(first_page_data['apartments'])
    print(f"✅ Найдено {ads_on_first_page} объявлений на первой странице.")

    next_token = first_page_data['next_page_token']
    if next_token:
        current_url = f"{BASE_URL}?cursor={next_token}"
    else:
        max_pages = 1

    # --- ШАГ 2: Запускаем основной цикл для остальных страниц ---
    if max_pages > 1:
        for page_num in range(2, max_pages + 1):
            print(
                f"\n--- 📄 Обрабатываю страницу №{page_num} из {max_pages} ---")

            print(f"Пауза {SLEEP_DELAY_SECONDS} сек...")
            time.sleep(SLEEP_DELAY_SECONDS)

            page_data = get_page_data(current_url)

            if not page_data or not page_data['apartments']:
                print(
                    "Не удалось получить данные или на странице нет объявлений. Завершаю.")
                break

            all_found_apartments.extend(page_data['apartments'])
            print(
                f"✅ Найдено {len(page_data['apartments'])} объявлений. Всего собрано: {len(all_found_apartments)}")

            next_token = page_data['next_page_token']
            if next_token:
                current_url = f"{BASE_URL}?cursor={next_token}"
            else:
                print("\n🏁 Это была последняя страница.")
                break

    print(
        f"\n\n🎉🎉🎉 Работа завершена! Всего собрано {len(all_found_apartments)} объявлений.")
