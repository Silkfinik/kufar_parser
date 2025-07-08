# find_dictionaries.py (temporary script)

import requests
import json
from bs4 import BeautifulSoup

URL = "https://re.kufar.by/l/minsk/snyat/kvartiru"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}


def find_list_by_fingerprint(data, path=""):
    """
    Универсальный рекурсивный поиск списка, похожего на список фильтров/словарей.
    """
    if isinstance(data, list) and len(data) > 0:
        first_item = data[0]
        if isinstance(first_item, dict):

            keys = first_item.keys()
            if ('label' in keys and 'values' in keys) or \
               ('label' in keys and 'options' in keys) or \
               ('name' in keys and 'values' in keys):

                print(f"🔥 НАЙДЕН ПОТЕНЦИАЛЬНЫЙ СПИСОК СЛОВАРЕЙ!")
                print(f"   ПУТЬ: data{path}")
                print(
                    f"   Пример первого элемента: {json.dumps(first_item, ensure_ascii=False, indent=2)}")

    if isinstance(data, dict):
        for key, value in data.items():
            find_list_by_fingerprint(value, f"{path}['{key}']")
    elif isinstance(data, list):
        for i, item in enumerate(data):
            find_list_by_fingerprint(item, f"{path}[{i}]")


print(f"Запускаю разведку на странице: {URL}")
try:
    response = requests.get(URL, headers=HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    script_tag = soup.find('script', id='__NEXT_DATA__')
    data = json.loads(script_tag.string)

    print("\n--- 🕵️‍♂️ Запускаю универсальный поиск словарей по 'отпечатку'... ---")
    find_list_by_fingerprint(data)
    print("\n--- Поиск завершен ---")

except Exception as e:
    print(f"Произошла ошибка: {e}")
