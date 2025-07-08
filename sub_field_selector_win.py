# sub_field_selector_win.py
import customtkinter as ctk
import json


class SubFieldSelectorWindow(ctk.CTkToplevel):
    """
    Окно для выбора вложенных полей с функцией предпросмотра и прокруткой колесиком.
    """

    def __init__(self, parent, sub_fields_data, previous_config):
        super().__init__(parent)
        self.transient(parent)
        self.title("Настройка вложенных полей")
        self.geometry("600x600")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.widgets = []
        self.result_config = previous_config

        self.scrollable_frame = ctk.CTkScrollableFrame(
            self, label_text="Параметр -> Имя столбца")
        self.scrollable_frame.grid(
            row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(1, weight=1)

        is_first_open = not previous_config

        for i, item in enumerate(sub_fields_data):
            field_name = item.get("pl")
            if not field_name:
                continue

            checkbox = ctk.CTkCheckBox(
                self.scrollable_frame, text=field_name, width=200)
            checkbox.grid(row=i, column=0, padx=10, pady=8, sticky="w")

            if is_first_open or field_name in self.result_config:
                checkbox.select()

            entry = ctk.CTkEntry(self.scrollable_frame)
            entry.grid(row=i, column=1, padx=5, pady=8, sticky="ew")
            entry.insert(0, self.result_config.get(field_name, field_name))

            preview_button = ctk.CTkButton(
                self.scrollable_frame, text="...", width=40, command=lambda v=item: self.show_preview(v))
            preview_button.grid(row=i, column=2, padx=10, pady=8, sticky="e")

            self.widgets.append(
                {'checkbox': checkbox, 'entry': entry, 'original_name': field_name})

        self.preview_textbox = ctk.CTkTextbox(
            self, height=100, font=("Courier New", 12))
        self.preview_textbox.grid(
            row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.preview_textbox.insert(
            "0.0", "Нажмите '...' для предпросмотра значения.")
        self.preview_textbox.configure(state="disabled")

        confirm_button = ctk.CTkButton(
            self, text="Подтвердить", command=self.confirm_selection)
        confirm_button.grid(row=2, column=0, columnspan=2,
                            padx=10, pady=10, sticky="ew")

        # --- НОВЫЙ КОД: Активируем прокрутку ---
        self.bind_mouse_scroll(self.scrollable_frame)
        for child in self.scrollable_frame.winfo_children():
            self.bind_mouse_scroll(child)

    def on_mouse_wheel(self, event):
        """Обрабатывает событие прокрутки колесика мыши."""
        if event.num == 4:  # Linux: scroll up
            self.scrollable_frame._parent_canvas.yview_scroll(-1, "units")
        elif event.num == 5:  # Linux: scroll down
            self.scrollable_frame._parent_canvas.yview_scroll(1, "units")
        else:  # Windows/macOS
            self.scrollable_frame._parent_canvas.yview_scroll(
                int(-1 * (event.delta / 120)), "units")

    def bind_mouse_scroll(self, widget):
        """Привязывает событие прокрутки к виджету и всем его дочерним элементам."""
        widget.bind("<MouseWheel>", self.on_mouse_wheel, add="+")
        widget.bind("<Button-4>", self.on_mouse_wheel, add="+")
        widget.bind("<Button-5>", self.on_mouse_wheel, add="+")
        if hasattr(widget, 'winfo_children'):
            for child in widget.winfo_children():
                self.bind_mouse_scroll(child)

    def show_preview(self, item):
        self.preview_textbox.configure(state="normal")
        self.preview_textbox.delete("0.0", "end")
        key = item.get("pl", "N/A")
        value_vl = item.get("vl")
        value_v = item.get("v")
        display_value = value_vl if value_vl not in [None, "", []] else value_v
        preview_text = f"Поле: '{key}'\nЗначение: {json.dumps(display_value, ensure_ascii=False, indent=2)}"
        self.preview_textbox.insert("0.0", preview_text)
        self.preview_textbox.configure(state="disabled")

    def confirm_selection(self):
        self.result_config = {
            w['original_name']: w['entry'].get()
            for w in self.widgets if w['checkbox'].get() == 1 and w['entry'].get()
        }
        self.destroy()
