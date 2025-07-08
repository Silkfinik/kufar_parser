# gui_app.py
# ... (импорты и функция process_and_flatten_data без изменений) ...
import customtkinter as ctk
import threading
import time
import math
import csv
import json
from scraper import get_page_data
from field_selector_win import FieldSelectorWindow


# gui_app.py
# ... (imports are the same) ...

# --- НОВАЯ УНИВЕРСАЛЬНАЯ ФУНКЦИЯ ОБРАБОТКИ ДАННЫХ ---
def process_and_flatten_data(apartment_list, selection_config, empty_symbol, list_separator):
    if not selection_config:
        return apartment_list, []

    processed_list = []
    field_map = selection_config.get("field_map", {})
    unpack_config = selection_config.get("unpacked_fields", {})

    # Собираем финальный список заголовков один раз
    final_headers = []
    for original_name, custom_name in field_map.items():
        if original_name not in unpack_config:
            final_headers.append(custom_name)
    for config in unpack_config.values():
        final_headers.extend(config['sub_field_map'].values())

    for ad in apartment_list:
        flat_ad = {}
        # 1. Обрабатываем простые и автоматически преобразуемые поля
        for original_name, custom_name in field_map.items():
            if original_name not in unpack_config:
                value = ad.get(original_name)

                if value is None or value == '':
                    flat_ad[custom_name] = empty_symbol
                elif isinstance(value, list):  # Авто-конвертация простых списков
                    flat_ad[custom_name] = list_separator.join(map(str, value))
                else:
                    flat_ad[custom_name] = value

        # 2. Распаковываем сложные поля согласно настройкам
        for field_to_unpack, config in unpack_config.items():
            # Если это список словарей (как ad_parameters)
            if config['type'] == 'list_of_dicts':
                param_lookup = {}
                if field_to_unpack in ad and ad[field_to_unpack]:
                    param_lookup = {str(item.get(config["source_key"])): item.get(config["value_key"])
                                    for item in ad[field_to_unpack] if config["source_key"] in item}
                for original_sub_name, custom_sub_name in config['sub_field_map'].items():
                    value = param_lookup.get(original_sub_name)
                    flat_ad[custom_sub_name] = value if value not in [
                        None, ""] else empty_symbol

            # Если это простой словарь (как paid_services)
            elif config['type'] == 'dict':
                source_dict = ad.get(field_to_unpack, {})
                for original_sub_name, custom_sub_name in config['sub_field_map'].items():
                    value = source_dict.get(original_sub_name)
                    flat_ad[custom_sub_name] = value if value not in [
                        None, ""] else empty_symbol

        processed_list.append(flat_ad)

    return processed_list, final_headers


class App(ctk.CTk):
    def __init__(self):
        # ... (код __init__ до настроек)
        super().__init__()
        self.title("Kufar Scraper ⚡")
        self.geometry("700x550")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.grid_columnconfigure(0, weight=1)
        self.url_frame = ctk.CTkFrame(self)
        self.url_frame.grid(row=0, column=0, padx=10,
                            pady=(10, 5), sticky="ew")
        self.url_frame.grid_columnconfigure(0, weight=1)
        self.url_label = ctk.CTkLabel(
            self.url_frame, text="Вставьте ссылку с настроенными фильтрами с re.kufar.by:", font=("Arial", 14, "bold"))
        self.url_label.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")
        self.url_entry = ctk.CTkEntry(
            self.url_frame, placeholder_text="https://re.kufar.by/l/minsk/snyat/kvartiru?price=r:100,500", height=35)
        self.url_entry.grid(row=1, column=0, padx=15,
                            pady=(5, 15), sticky="ew")

        # --- ОБНОВЛЕННЫЙ ФРЕЙМ НАСТРОЕК ---
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.settings_frame.grid_columnconfigure((0, 1), weight=1)

        self.delay_label = ctk.CTkLabel(
            self.settings_frame, text="Задержка (сек):")
        self.delay_label.grid(row=0, column=0, padx=15, pady=10, sticky="w")
        self.delay_entry = ctk.CTkEntry(self.settings_frame, width=60)
        self.delay_entry.grid(row=0, column=0, padx=(
            115, 0), pady=10, sticky="w")
        self.delay_entry.insert(0, "1")

        self.empty_label = ctk.CTkLabel(
            self.settings_frame, text="Заполнитель пустых полей:")
        self.empty_label.grid(row=0, column=1, padx=15, pady=10, sticky="w")
        self.empty_entry = ctk.CTkEntry(self.settings_frame, width=80)
        self.empty_entry.grid(row=0, column=1, padx=(
            190, 0), pady=10, sticky="w")
        self.empty_entry.insert(0, "N/A")

        # НОВАЯ НАСТРОЙКА
        self.separator_label = ctk.CTkLabel(
            self.settings_frame, text="Разделитель для списков:")
        self.separator_label.grid(
            row=1, column=0, padx=15, pady=10, sticky="w")
        self.separator_entry = ctk.CTkEntry(self.settings_frame, width=60)
        self.separator_entry.grid(
            row=1, column=0, padx=(190, 0), pady=10, sticky="w")
        self.separator_entry.insert(0, ", ")

        # ... (остальные виджеты и функции до main_scraping_worker без изменений)
        self.format_segmented_button = ctk.CTkSegmentedButton(
            self, values=["CSV", "JSON"], height=35)
        self.format_segmented_button.set("CSV")
        self.format_segmented_button.grid(
            row=2, column=0, padx=20, pady=10, sticky="w")
        self.start_button = ctk.CTkButton(self, text="Начать анализ и настройку",
                                          command=self.start_initial_fetch, height=40, font=("Arial", 16, "bold"))
        self.start_button.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.progress_bar = ctk.CTkProgressBar(self, mode="indeterminate")
        self.status_textbox = ctk.CTkTextbox(
            self, state="disabled", font=("Courier New", 12))
        self.status_textbox.grid(
            row=4, column=0, padx=10, pady=10, sticky="nsew")
        self.grid_rowconfigure(4, weight=1)
        self.first_page_data = None
        self.base_url = ""

    def log_status(self, message):
        def _log():
            self.status_textbox.configure(state="normal")
            self.status_textbox.insert("end", message + "\n")
            self.status_textbox.see("end")
            self.status_textbox.configure(state="disabled")
        self.after(0, _log)

    def set_ui_state(self, is_running):
        state = "disabled" if is_running else "normal"
        button_text = "В процессе..." if is_running else "Начать анализ и настройку"
        self.start_button.configure(state=state, text=button_text)
        self.url_entry.configure(state=state)
        self.delay_entry.configure(state=state)
        self.empty_entry.configure(state=state)
        self.separator_entry.configure(state=state)
        self.format_segmented_button.configure(state=state)
        if is_running:
            self.progress_bar.grid(
                row=5, column=0, padx=10, pady=10, sticky="ew")
            self.progress_bar.start()
        else:
            self.progress_bar.stop()
            self.progress_bar.grid_forget()

    def start_initial_fetch(self):
        self.base_url = self.url_entry.get()
        if not self.base_url.startswith("https://re.kufar.by/"):
            self.log_status(
                "❌ ОШИБКА: Пожалуйста, вставьте корректную ссылку с re.kufar.by")
            return
        self.set_ui_state(is_running=True)
        self.log_status("🚀 Запуск... Анализирую первую страницу...")
        thread = threading.Thread(target=self.initial_fetch_worker)
        thread.start()

    def initial_fetch_worker(self):
        self.first_page_data = get_page_data(self.base_url)
        if not self.first_page_data or self.first_page_data.get("error"):
            self.log_status(
                f"❌ ОШИБКА: {self.first_page_data.get('error', 'Неизвестная ошибка')}")
            self.set_ui_state(is_running=False)
            return
        total_ads = self.first_page_data.get('total_ads', 0)
        ads_on_page = len(self.first_page_data.get('apartments', []))
        if ads_on_page == 0:
            self.log_status(
                "❌ На первой странице не найдено объявлений. Проверьте ссылку.")
            self.set_ui_state(is_running=False)
            return
        self.max_pages = math.ceil(total_ads / ads_on_page)
        self.log_status(
            f"📊 Анализ завершен. Всего найдено {total_ads} объявлений (~{self.max_pages} страниц).")
        self.after(0, self.prompt_user_for_all_settings)

    def prompt_user_for_all_settings(self):
        self.dialog_result = None
        sample_ad = self.first_page_data['apartments'][0]
        selector_window = FieldSelectorWindow(self, sample_ad, self.max_pages)
        self.wait_window(selector_window)
        full_config = self.dialog_result
        if full_config is None:
            self.log_status("🛑 Операция отменена на этапе настройки.")
            self.set_ui_state(is_running=False)
            return
        selection_config = full_config["selection_config"]
        pages_to_scrape = full_config["pages_to_scrape"]
        self.log_status(
            f"✅ Настройки сохранены. Будет обработано: {pages_to_scrape} страниц.")
        main_thread = threading.Thread(
            target=self.main_scraping_worker, args=(pages_to_scrape, selection_config))
        main_thread.start()

    def main_scraping_worker(self, pages_to_scrape, selection_config):
        # ... (цикл сбора данных без изменений)
        all_found_apartments = self.first_page_data['apartments']
        next_token = self.first_page_data.get('next_page_token')
        current_url = self.base_url
        delay = float(self.delay_entry.get() or "1")
        self.log_status(
            f"✅ Найдено {len(all_found_apartments)} объявлений на странице №1.")
        if pages_to_scrape > 1:
            for page_num in range(2, pages_to_scrape + 1):
                if not next_token:
                    self.log_status("🏁 Больше страниц нет.")
                    break
                base_url_without_cursor = current_url.split('?')[0]
                current_url = f"{base_url_without_cursor}?cursor={next_token}"
                self.log_status(
                    f"--- 📄 Обрабатываю страницу №{page_num} из {pages_to_scrape} ---")
                time.sleep(delay)
                page_data = get_page_data(current_url)
                if not page_data or page_data.get("error"):
                    self.log_status(
                        f"❌ ОШИБКА: {page_data.get('error', 'Неизвестная ошибка')}")
                    continue
                all_found_apartments.extend(page_data['apartments'])
                self.log_status(
                    f"✅ Найдено {len(page_data['apartments'])} объявлений. Всего собрано: {len(all_found_apartments)}")
                next_token = page_data.get('next_page_token')

        # --- ОБРАБАТЫВАЕМ И СОХРАНЯЕМ ---
        self.log_status(
            f"\n🎉 Сбор завершен! Всего найдено {len(all_found_apartments)} объявлений.")
        self.log_status(
            "Обрабатываю и 'расплющиваю' данные согласно настройкам...")

        empty_symbol = self.empty_entry.get()
        list_separator = self.separator_entry.get()
        processed_data, final_headers = process_and_flatten_data(
            all_found_apartments, selection_config, empty_symbol, list_separator)

        file_format = self.format_segmented_button.get().lower()
        filename = f"kufar_ads_{int(time.time())}"
        self.save_results(processed_data, final_headers, file_format, filename)
        self.set_ui_state(is_running=False)

    def save_results(self, processed_data, headers, file_format, filename):
        # ... (функция save_results теперь почти идеальна и не требует изменений)
        if not processed_data:
            return
        full_filename = f"{filename}.{file_format}"
        self.log_status(f"💾 Сохраняю данные в {full_filename}...")
        try:
            if file_format == "csv":
                with open(full_filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(processed_data)
            elif file_format == "json":
                with open(full_filename, 'w', encoding='utf-8') as f:
                    json.dump(processed_data, f, ensure_ascii=False, indent=4)
            self.log_status(f"✅ Файл успешно сохранен!")
        except Exception as e:
            self.log_status(f"❌ Ошибка сохранения: {e}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
