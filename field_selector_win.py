# field_selector_win.py
import customtkinter as ctk
import json
from sub_field_selector_win import SubFieldSelectorWindow  # <-- НОВЫЙ ИМПОРТ


class FieldSelectorWindow(ctk.CTkToplevel):
    def __init__(self, parent, sample_ad_data):
        super().__init__(parent)
        self.transient(parent)
        self.title("Выбор полей для экспорта")
        self.geometry("600x700")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sample_ad_data = sample_ad_data
        self.checkboxes = {}
        self.unpacked_fields_config = {}  # <-- ЗДЕСЬ ХРАНИМ ВЫБОР ВЛОЖЕННЫХ ПОЛЕЙ
        self.selection_result = None

        scrollable_frame = ctk.CTkScrollableFrame(
            self, label_text="Выберите поля или распакуйте сложные")
        scrollable_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        scrollable_frame.grid_columnconfigure(0, weight=1)

        for i, (key, value) in enumerate(sample_ad_data.items()):
            checkbox = ctk.CTkCheckBox(scrollable_frame, text=key)
            checkbox.grid(row=i, column=0, padx=10, pady=5, sticky="w")
            checkbox.select()
            self.checkboxes[key] = checkbox

            # --- ОБНОВЛЕННАЯ ЛОГИКА: ДОБАВЛЯЕМ КНОПКУ "РАСПАКОВАТЬ" ---
            is_unpackable = isinstance(value, list) and len(
                value) > 0 and isinstance(value[0], dict) and 'pl' in value[0]

            if is_unpackable:
                unpack_button = ctk.CTkButton(scrollable_frame, text="Распаковать...", width=120,
                                              command=lambda k=key, v=value: self.open_sub_field_selector(k, v))
                unpack_button.grid(row=i, column=1, padx=5, pady=5, sticky="e")
            else:
                preview_button = ctk.CTkButton(scrollable_frame, text="Предпросмотр", width=120,
                                               command=lambda k=key, v=value: self.show_preview(k, v))
                preview_button.grid(
                    row=i, column=1, padx=5, pady=5, sticky="e")

        self.preview_textbox = ctk.CTkTextbox(
            self, height=150, font=("Courier New", 12))
        self.preview_textbox.grid(
            row=1, column=0, padx=10, pady=10, sticky="ew")
        self.preview_textbox.insert(
            "0.0", "Нажмите 'Предпросмотр' или 'Распаковать'...")
        self.preview_textbox.configure(state="disabled")

        confirm_button = ctk.CTkButton(
            self, text="Подтвердить выбор и продолжить", command=self.confirm_selection, height=35)
        confirm_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

    def open_sub_field_selector(self, key, value):
        """Открывает окно выбора вложенных полей."""
        # Собираем имена всех вложенных полей. 'pl' - это их имя (parameter label)
        sub_field_names = [item.get('pl') for item in value if item.get('pl')]

        # Получаем предыдущий выбор для этого ключа, если он был
        previous_selection = self.unpacked_fields_config.get(
            key, {}).get('selected_sub_fields', [])

        sub_window = SubFieldSelectorWindow(
            self, sub_field_names, previous_selection)
        self.wait_window(sub_window)  # Ждем, пока пользователь сделает выбор

        # Сохраняем выбор пользователя
        if hasattr(sub_window, 'selected_sub_fields'):
            self.unpacked_fields_config[key] = {
                "selected_sub_fields": sub_window.selected_sub_fields,
                "source_key": "pl",  # ключ, где лежит имя параметра
                "value_key": "vl"   # ключ, где лежит значение параметра
            }
            self.show_preview(key, self.unpacked_fields_config[key])
            self.master.log_status(
                f"⚙️ Для поля '{key}' настроена распаковка {len(sub_window.selected_sub_fields)} вложенных полей.")

    def show_preview(self, key, value):
        self.preview_textbox.configure(state="normal")
        self.preview_textbox.delete("0.0", "end")
        preview_text = f"--- Предпросмотр поля: '{key}' ---\n\n"
        if isinstance(value, (dict, list)):
            preview_text += json.dumps(value, ensure_ascii=False, indent=2)
        else:
            preview_text += str(value)
        self.preview_textbox.insert("0.0", preview_text)
        self.preview_textbox.configure(state="disabled")

    def confirm_selection(self):
        # Собираем базовые поля
        selected_top_level_fields = [
            key for key, checkbox in self.checkboxes.items() if checkbox.get() == 1]

        # Сохраняем итоговый результат
        self.selection_result = {
            "top_level_fields": selected_top_level_fields,
            "unpacked_fields": self.unpacked_fields_config
        }
        self.destroy()
