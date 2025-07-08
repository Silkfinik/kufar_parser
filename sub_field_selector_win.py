# sub_field_selector_win.py
import customtkinter as ctk


class SubFieldSelectorWindow(ctk.CTkToplevel):
    """
    Окно для выбора вложенных полей из сложного объекта (например, ad_parameters).
    """

    def __init__(self, parent, sub_fields_data, previous_selection):
        super().__init__(parent)
        self.transient(parent)
        self.title("Выберите вложенные поля")
        self.geometry("500x600")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.checkboxes = {}
        self.selected_sub_fields = previous_selection  # Восстанавливаем предыдущий выбор

        scrollable_frame = ctk.CTkScrollableFrame(
            self, label_text="Параметры для добавления в столбцы")
        scrollable_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        for i, field_name in enumerate(sub_fields_data):
            checkbox = ctk.CTkCheckBox(scrollable_frame, text=field_name)
            checkbox.grid(row=i, column=0, padx=10, pady=5, sticky="w")
            if field_name in self.selected_sub_fields:
                checkbox.select()  # Отмечаем, если было выбрано ранее
            self.checkboxes[field_name] = checkbox

        confirm_button = ctk.CTkButton(
            self, text="Подтвердить", command=self.confirm_selection)
        confirm_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

    def confirm_selection(self):
        self.selected_sub_fields = [
            key for key, checkbox in self.checkboxes.items() if checkbox.get() == 1]
        self.destroy()
