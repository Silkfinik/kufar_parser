# gui_app.py

import customtkinter as ctk
import threading
import time
import math
import csv
import json
from scraper import get_page_data
# --- НОВЫЙ ИМПОРТ ---
from field_selector_win import FieldSelectorWindow

# --- Основной класс приложения ---


class App(ctk.CTk):
    # ... (весь код __init__ и других функций остается без изменений до prompt_for_page_count) ...
    # ... (я пропущу дублирование для краткости)
    def __init__(self):
        super().__init__()
        # ... (вся ваша предыдущая настройка виджетов)
        self.title("Kufar Scraper ⚡")
        self.geometry("700x650")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.grid_columnconfigure(0, weight=1)
        self.url_frame = ctk.CTkFrame(self)
        self.url_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.url_frame.grid_columnconfigure(0, weight=1)
        self.url_label = ctk.CTkLabel(
            self.url_frame, text="Вставьте ссылку с настроенными фильтрами с re.kufar.by:", font=("Arial", 14, "bold"))
        self.url_label.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")
        self.url_entry = ctk.CTkEntry(
            self.url_frame, placeholder_text="https://re.kufar.by/l/minsk/snyat/kvartiru?price=r:100,500", height=35)
        self.url_entry.grid(row=1, column=0, padx=15,
                            pady=(5, 15), sticky="ew")
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.grid(
            row=1, column=0, padx=10, pady=10, sticky="ew")
        self.settings_frame.grid_columnconfigure(0, weight=1)
        self.settings_frame.grid_columnconfigure(1, weight=1)
        self.ask_pages_switch = ctk.CTkSwitch(
            self.settings_frame, text="Спрашивать кол-во страниц", font=("Arial", 12), onvalue=True, offvalue=False)
        self.ask_pages_switch.grid(
            row=0, column=0, padx=15, pady=15, sticky="w")
        self.ask_pages_switch.select()
        self.delay_label = ctk.CTkLabel(
            self.settings_frame, text="Задержка (сек):", font=("Arial", 12))
        self.delay_label.grid(row=0, column=1, padx=(
            100, 5), pady=15, sticky="w")
        self.delay_entry = ctk.CTkEntry(self.settings_frame, width=60)
        self.delay_entry.grid(row=0, column=1, padx=(
            200, 15), pady=15, sticky="w")
        self.delay_entry.insert(0, "1")
        self.format_segmented_button = ctk.CTkSegmentedButton(
            self, values=["CSV", "JSON"], height=35)
        self.format_segmented_button.set("CSV")
        self.format_segmented_button.grid(
            row=2, column=0, padx=20, pady=10, sticky="w")
        self.start_button = ctk.CTkButton(
            self, text="Начать анализ", command=self.start_initial_fetch, height=40, font=("Arial", 16, "bold"))
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
        button_text = "В процессе..." if is_running else "Начать анализ"
        self.start_button.configure(state=state, text=button_text)
        self.url_entry.configure(state=state)
        self.ask_pages_switch.configure(state=state)
        self.delay_entry.configure(state=state)
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
        self.after(0, self.prompt_user_for_next_steps)

    ### --- ОБНОВЛЕННАЯ ЛОГИКА --- ###
    def prompt_user_for_next_steps(self):
        """
        Показывает окна выбора полей и выбора количества страниц, затем запускает основной парсер.
        """
        # --- ШАГ 2.1: Выбор полей для экспорта ---
        self.log_status(
            "Пожалуйста, выберите поля для экспорта в появившемся окне...")
        sample_ad = self.first_page_data['apartments'][0]
        selector_window = FieldSelectorWindow(self, sample_ad)
        # Ждем, пока пользователь закроет окно выбора полей
        self.wait_window(selector_window)

        selected_fields = selector_window.selected_fields
        if selected_fields is None:  # Пользователь закрыл окно крестиком
            self.log_status("🛑 Операция отменена. Выбор полей не сделан.")
            self.set_ui_state(is_running=False)
            return
        self.log_status(f"Выбрано полей для экспорта: {len(selected_fields)}.")

        # --- ШАГ 2.2: Выбор количества страниц ---
        pages_to_scrape = self.max_pages
        if self.ask_pages_switch.get() is True:
            dialog = ctk.CTkInputDialog(
                text=f"Найдено {self.max_pages} страниц.\nСколько страниц обработать?", title="Выбор количества страниц")
            user_input = dialog.get_input()
            if user_input is None:
                self.log_status("🛑 Операция отменена пользователем.")
                self.set_ui_state(is_running=False)
                return
            try:
                pages_to_scrape = min(self.max_pages, int(user_input))
            except (ValueError, TypeError):
                self.log_status(
                    f"⚠️ Ввод не распознан. Будут обработаны все {self.max_pages} страниц.")

        self.log_status(f"⚙️ Принято к обработке: {pages_to_scrape} страниц.")

        # --- ШАГ 2.3: Запуск основного сбора ---
        main_thread = threading.Thread(
            target=self.main_scraping_worker, args=(pages_to_scrape, selected_fields))
        main_thread.start()

    def main_scraping_worker(self, pages_to_scrape, selected_fields):
        # ... (Эта функция теперь принимает 'selected_fields')
        all_found_apartments = self.first_page_data['apartments']
        next_token = self.first_page_data.get('next_page_token')
        current_url = self.base_url
        delay = float(self.delay_entry.get() or "1")

        self.log_status(
            f"✅ Найдено {len(all_found_apartments)} объявлений на странице №1.")

        if pages_to_scrape > 1:
            for page_num in range(2, pages_to_scrape + 1):
                # ... (логика цикла остается прежней) ...
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

        # --- Передаем selected_fields в функцию сохранения ---
        file_format = self.format_segmented_button.get().lower()
        filename = f"kufar_ads_{int(time.time())}"
        self.log_status(
            f"\n🎉 Сбор завершен! Всего найдено {len(all_found_apartments)} объявлений.")
        self.save_results(all_found_apartments, file_format,
                          filename, selected_fields)
        self.set_ui_state(is_running=False)

    def save_results(self, apartments, file_format, filename, selected_fields):
        # --- Функция сохранения теперь использует selected_fields ---
        if not apartments:
            return
        full_filename = f"{filename}.{file_format}"
        self.log_status(f"💾 Сохраняю данные в {full_filename}...")

        # --- Фильтруем данные перед сохранением ---
        filtered_apartments = []
        for ad in apartments:
            filtered_ad = {key: ad.get(key) for key in selected_fields}
            filtered_apartments.append(filtered_ad)

        try:
            if file_format == "csv":
                processed_for_csv = []
                for ad in filtered_apartments:
                    processed_ad = {k: json.dumps(v, ensure_ascii=False) if isinstance(
                        v, (dict, list)) else v for k, v in ad.items()}
                    processed_for_csv.append(processed_ad)

                with open(full_filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=selected_fields)
                    writer.writeheader()
                    writer.writerows(processed_for_csv)
            elif file_format == "json":
                with open(full_filename, 'w', encoding='utf-8') as f:
                    json.dump(filtered_apartments, f,
                              ensure_ascii=False, indent=4)
            self.log_status(f"✅ Файл успешно сохранен!")
        except Exception as e:
            self.log_status(f"❌ Ошибка сохранения: {e}")


# --- Запуск приложения ---
if __name__ == "__main__":
    app = App()
    app.mainloop()
