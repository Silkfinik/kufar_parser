import requests
import json
from bs4 import BeautifulSoup

URL = "https://re.kufar.by/l/minsk/snyat/kvartiru"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}


def find_list_by_fingerprint(data, path=""):
    """
    Ищет список, элементы которого являются словарями и содержат ключ 'ad_link'.
    """
    # 1. Если текущий элемент - это непустой список
    if isinstance(data, list) and len(data) > 0:
        first_item = data[0]
        # 2. И если первый элемент списка - это словарь, содержащий наш "отпечаток"
        if isinstance(first_item, dict) and 'ad_link' in first_item:
            print(f"🔥 НАЙДЕН ПОТЕНЦИАЛЬНЫЙ СПИСОК ОБЪЯВЛЕНИЙ!")
            print(f"   ПУТЬ: data{path}")
            print(f"   Количество элементов: {len(data)}")
            # Мы не будем выводить весь элемент, чтобы не засорять консоль
            print(
                f"   Пример ключей первого элемента: {list(first_item.keys())}")

    # 3. Рекурсивно продолжаем поиск вглубь структуры
    if isinstance(data, dict):
        for key, value in data.items():
            find_list_by_fingerprint(value, f"{path}['{key}']")
    elif isinstance(data, list):
        for i, item in enumerate(data):
            find_list_by_fingerprint(item, f"{path}[{i}]")


# --- Основная часть ---
print(f"Запускаю разведку V2 на странице: {URL}")

try:
    response = requests.get(URL, headers=HEADERS)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    print(f"Ошибка при запросе страницы: {e}")
    exit()

soup = BeautifulSoup(response.text, 'html.parser')
script_tag = soup.find('script', id='__NEXT_DATA__')
if not script_tag:
    exit("Не удалось найти тег <script id='__NEXT_DATA__'>.")

try:
    data = json.loads(script_tag.string)
except json.JSONDecodeError:
    exit("Ошибка декодирования JSON.")

print("\n--- Ищу список по 'отпечатку' (ключ 'ad_link' в элементах) ---")
find_list_by_fingerprint(data)
print("\n--- Разведка V2 завершена ---")
