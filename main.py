# main.py

import time
import math
import csv
import json
from config import BASE_URL, MAX_PAGES_TO_SCRAPE, AUTO_DETECT_PAGES, SLEEP_DELAY_SECONDS, EXPORT_FORMAT, EXPORT_FILENAME
from scraper import get_page_data


def save_results(apartments, file_format, filename):
    """
    Сохраняет собранные данные в файл указанного формата (csv или json).
    """
    if not apartments:
        print("Нет данных для сохранения.")
        return

    full_filename = f"{filename}.{file_format}"
    print(
        f"\n💾 Сохраняю {len(apartments)} объявлений в файл {full_filename}...")

    if file_format == "csv":
        try:
            # Для CSV нужно обработать вложенные структуры (списки, словари)
            processed_apartments = []
            for ad in apartments:
                processed_ad = {}
                for key, value in ad.items():
                    if isinstance(value, (dict, list)):
                        # Преобразуем сложные поля в строку JSON, чтобы они поместились в одну ячейку
                        processed_ad[key] = json.dumps(
                            value, ensure_ascii=False)
                    else:
                        processed_ad[key] = value
                processed_apartments.append(processed_ad)

            # Используем ключи первого обработанного объявления как заголовки
            headers = processed_apartments[0].keys()
            with open(full_filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=headers)
                writer.writeheader()
                writer.writerows(processed_apartments)
            print("✅ Данные успешно сохранены в CSV.")

        except Exception as e:
            print(f"❌ Ошибка при сохранении в CSV: {e}")

    elif file_format == "json":
        try:
            with open(full_filename, 'w', encoding='utf-8') as file:
                json.dump(apartments, file, ensure_ascii=False, indent=4)
            print("✅ Данные успешно сохранены в JSON.")
        except Exception as e:
            print(f"❌ Ошибка при сохранении в JSON: {e}")
    else:
        print(
            f"⚠️ Неизвестный формат для сохранения: {file_format}. Допустимые форматы: 'csv', 'json'.")


if __name__ == "__main__":
    all_found_apartments = []
    current_url = BASE_URL
    pages_to_scrape = MAX_PAGES_TO_SCRAPE

    # ... (весь код для сбора данных остается таким же, как в прошлый раз) ...
    # --- ШАГ 1: Определяем, сколько страниц обрабатывать ---
    print("🚀 Запуск парсера...")

    first_page_data = get_page_data(current_url)
    if not first_page_data:
        exit("❌ Не удалось загрузить первую страницу. Завершение работы.")

    if AUTO_DETECT_PAGES:
        total_ads = first_page_data.get('total_ads', 0)
        ads_per_page = len(first_page_data.get('apartments', [1]))
        if total_ads > 0 and ads_per_page > 0:
            pages_to_scrape = math.ceil(total_ads / ads_per_page)
            print(
                f"📊 Автоопределение: найдено {total_ads} объявлений. Требуется обработать ~{pages_to_scrape} страниц.")
        else:
            pages_to_scrape = 1
    else:
        print(
            f"⚙️ Установлен ручной режим: будет обработано {pages_to_scrape} страниц.")

    all_found_apartments.extend(first_page_data['apartments'])
    print(
        f"✅ Найдено {len(first_page_data['apartments'])} объявлений на странице №1.")

    next_token = first_page_data['next_page_token']
    if not next_token:
        pages_to_scrape = 1

    # --- ШАГ 2: Запускаем основной цикл для остальных страниц ---
    if pages_to_scrape > 1:
        for page_num in range(2, pages_to_scrape + 1):
            current_url = f"{BASE_URL}?cursor={next_token}"
            print(
                f"\n--- 📄 Обрабатываю страницу №{page_num} из {pages_to_scrape} ---")

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
            if not next_token:
                print("\n🏁 Это была последняя страница.")
                break

    print(
        f"\n\n🎉🎉🎉 Работа завершена! Всего собрано {len(all_found_apartments)} объявлений.")

    # --- ШАГ 3: Сохраняем результаты ---
    save_results(all_found_apartments, EXPORT_FORMAT, EXPORT_FILENAME)
