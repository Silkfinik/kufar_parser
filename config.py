# config.py

# --- ОСНОВНЫЕ НАСТРОЙКИ ПОИСКА ---
# URL для поиска. Позже мы научимся его генерировать с фильтрами.
BASE_URL = "https://re.kufar.by/l/minsk/snyat/kvartiru"

# --- НАСТРОЙКИ ПАГИНАЦИИ ---
# True — скрипт сам определит, сколько всего страниц, и пройдет по всем.
# False — скрипт будет использовать значение MAX_PAGES_TO_SCRAPE.
AUTO_DETECT_PAGES = False

# Сколько страниц обработать, если AUTO_DETECT_PAGES = False.
MAX_PAGES_TO_SCRAPE = 5

# --- ПРОЧИЕ НАСТРОЙКИ ---
# Задержка между запросами в секундах, чтобы не заблокировали.
SLEEP_DELAY_SECONDS = 2

# --- НАСТРОЙКИ ЭКСПОРТА ---
# В каком формате сохранить результат: "csv" или "json".
EXPORT_FORMAT = "csv"

# Имя файла для сохранения (без расширения).
EXPORT_FILENAME = "kufar_apartments"
