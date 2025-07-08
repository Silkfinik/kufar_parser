import customtkinter as ctk
import json
from sub_field_selector_win import SubFieldSelectorWindow


class FieldSelectorWindow(ctk.CTkToplevel):
    def __init__(self, parent, sample_ad_data, max_pages):
        super().__init__(parent)
        self.parent_app = parent
        self.transient(parent)
        self.title("Выбор и настройка полей для экспорта")
        self.geometry("700x750")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sample_ad_data = sample_ad_data
        self.max_pages = max_pages
        self.widgets = []
        self.unpacked_fields_config = {}
        self.last_clicked_key = None

        self.scrollable_frame = ctk.CTkScrollableFrame(
            self, label_text="Поле -> Имя столбца")
        self.scrollable_frame.grid(
            row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(1, weight=1)

        for i, (key, value) in enumerate(sample_ad_data.items()):
            checkbox = ctk.CTkCheckBox(
                self.scrollable_frame, text=key, width=200)
            checkbox.grid(row=i, column=0, padx=10, pady=8, sticky="w")
            checkbox.select()

            entry = ctk.CTkEntry(self.scrollable_frame)
            entry.grid(row=i, column=1, padx=5, pady=8, sticky="ew")
            entry.insert(0, key)

            button_frame = ctk.CTkFrame(
                self.scrollable_frame, fg_color="transparent")
            button_frame.grid(row=i, column=2, padx=5, pady=8, sticky="e")

            # Определяем, можно ли поле распаковать
            is_dict = isinstance(value, dict)
            is_list_of_dicts = isinstance(value, list) and len(
                value) > 0 and isinstance(value[0], dict)

            if is_dict or is_list_of_dicts:
                unpack_button = ctk.CTkButton(button_frame, text="Распаковать...", width=100,
                                              command=lambda k=key, v=value: self.open_sub_field_selector(k, v))
                unpack_button.pack(side="left")

            preview_button = ctk.CTkButton(
                button_frame, text="...", width=40, command=lambda k=key, v=value: self.show_preview(k, v))
            preview_button.pack(side="left", padx=(5, 0))
            self.widgets.append(
                {'checkbox': checkbox, 'entry': entry, 'original_name': key})

        self.preview_textbox = ctk.CTkTextbox(self, height=150)
        self.preview_textbox.grid(
            row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.preview_textbox.insert(
            "0.0", "Нажмите '...' или 'Распаковать'...")
        self.preview_textbox.configure(state="disabled")
        pages_frame = ctk.CTkFrame(self)
        pages_frame.grid(row=2, column=0, columnspan=2,
                         padx=10, pady=5, sticky="ew")
        pages_label = ctk.CTkLabel(
            pages_frame, text=f"Найдено страниц: {self.max_pages}. Сколько обработать?")
        pages_label.pack(side="left", padx=15, pady=10)
        self.pages_entry = ctk.CTkEntry(pages_frame, width=80)
        self.pages_entry.pack(side="left", padx=15, pady=10)
        self.pages_entry.insert(0, str(self.max_pages))
        confirm_button = ctk.CTkButton(
            self, text="Подтвердить и запустить парсинг", command=self.confirm_selection, height=40)
        confirm_button.grid(row=3, column=0, columnspan=2,
                            padx=10, pady=10, sticky="ew")
        self.bind_mouse_scroll(self.scrollable_frame)
        for child in self.scrollable_frame.winfo_children():
            self.bind_mouse_scroll(child)

    def open_sub_field_selector(self, key, value):
        self.last_clicked_key = key
        previous_config = self.unpacked_fields_config.get(
            key, {}).get('sub_field_map', {})

        unpack_type = None
        if isinstance(value, dict):
            unpack_type = 'dict'
        elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
            unpack_type = 'list_of_dicts'

        if not unpack_type:
            self.show_preview(key, "Этот тип поля нельзя распаковать.")
            return

        sub_window = SubFieldSelectorWindow(
            self, value, previous_config, unpack_type)
        self.wait_window(sub_window)

        if hasattr(sub_window, 'result_config') and sub_window.result_config:
            self.unpacked_fields_config[key] = {
                "type": unpack_type,
                "sub_field_map": sub_window.result_config,
                "source_key": "pl",
                "value_key": "v"
            }
            self.show_preview(key, {"Распаковано полей": list(
                sub_window.result_config.values())})
            self.parent_app.log_status(
                f"⚙️ Для поля '{key}' настроена распаковка {len(sub_window.result_config)} вложенных полей.")

    def on_mouse_wheel(self, event):
        if event.num == 4:
            self.scrollable_frame._parent_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.scrollable_frame._parent_canvas.yview_scroll(1, "units")
        else:
            self.scrollable_frame._parent_canvas.yview_scroll(
                int(-1 * (event.delta / 120)), "units")

    def bind_mouse_scroll(self, widget):
        widget.bind("<MouseWheel>", self.on_mouse_wheel, add="+")
        widget.bind("<Button-4>", self.on_mouse_wheel, add="+")
        widget.bind("<Button-5>", self.on_mouse_wheel, add="+")
        if hasattr(widget, 'winfo_children'):
            for child in widget.winfo_children():
                self.bind_mouse_scroll(child)

    def confirm_selection(self):
        field_config = {
            "field_map": {w['original_name']: w['entry'].get() for w in self.widgets if w['checkbox'].get() == 1 and w['entry'].get()},
            "unpacked_fields": self.unpacked_fields_config
        }
        try:
            pages_to_scrape = min(self.max_pages, int(self.pages_entry.get()))
            if pages_to_scrape <= 0:
                pages_to_scrape = 1
        except (ValueError, TypeError):
            pages_to_scrape = self.max_pages
        self.parent_app.dialog_result = {
            "selection_config": field_config,
            "pages_to_scrape": pages_to_scrape
        }
        self.destroy()

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
