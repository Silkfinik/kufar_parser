# field_selector_win.py
import customtkinter as ctk
import json


class FieldSelectorWindow(ctk.CTkToplevel):
    """
    Класс для создания модального окна выбора полей для экспорта.
    """

    def __init__(self, parent, sample_ad_data):
        super().__init__(parent)
        self.transient(parent)  # Привязываем окно к родительскому
        self.title("Выбор полей для экспорта")
        self.geometry("600x700")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sample_ad_data = sample_ad_data
        self.checkboxes = {}
        self.selected_fields = None  # Сюда запишется результат

        # --- Фрейм с прокруткой для списка полей ---
        scrollable_frame = ctk.CTkScrollableFrame(
            self, label_text="Выберите поля")
        scrollable_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        scrollable_frame.grid_columnconfigure(0, weight=1)

        # --- Создание чекбоксов и кнопок предпросмотра ---
        for i, (key, value) in enumerate(sample_ad_data.items()):
            checkbox = ctk.CTkCheckBox(scrollable_frame, text=key)
            checkbox.grid(row=i, column=0, padx=10, pady=5, sticky="w")
            checkbox.select()  # По умолчанию все поля выбраны
            self.checkboxes[key] = checkbox

            preview_button = ctk.CTkButton(scrollable_frame, text="Предпросмотр", width=100,
                                           command=lambda k=key, v=value: self.show_preview(k, v))
            preview_button.grid(row=i, column=1, padx=10, pady=5, sticky="e")

        # --- Панель для предпросмотра ---
        self.preview_textbox = ctk.CTkTextbox(
            self, height=150, font=("Courier New", 12))
        self.preview_textbox.grid(
            row=1, column=0, padx=10, pady=10, sticky="ew")
        self.preview_textbox.insert(
            "0.0", "Нажмите 'Предпросмотр', чтобы увидеть содержимое поля здесь...")
        self.preview_textbox.configure(state="disabled")

        # --- Кнопка подтверждения ---
        confirm_button = ctk.CTkButton(
            self, text="Подтвердить выбор и продолжить", command=self.confirm_selection, height=35)
        confirm_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

    def show_preview(self, key, value):
        """Показывает содержимое поля в панели предпросмотра."""
        self.preview_textbox.configure(state="normal")
        self.preview_textbox.delete("0.0", "end")

        preview_text = f"--- Предпросмотр поля: '{key}' ---\n\n"
        # Если значение - сложный объект, форматируем его красиво
        if isinstance(value, (dict, list)):
            preview_text += json.dumps(value, ensure_ascii=False, indent=2)
        else:
            preview_text += str(value)

        self.preview_textbox.insert("0.0", preview_text)
        self.preview_textbox.configure(state="disabled")

    def confirm_selection(self):
        """Собирает выбранные поля и закрывает окно."""
        self.selected_fields = [
            key for key, checkbox in self.checkboxes.items() if checkbox.get() == 1]
        if not self.selected_fields:
            # Если пользователь ничего не выбрал, выбираем хотя бы ссылку
            self.selected_fields = ['ad_link']
            self.master.log_status(
                "⚠️ Поля не выбраны. Будет экспортировано только поле 'ad_link'.")

        self.destroy()  # Закрываем это окно
