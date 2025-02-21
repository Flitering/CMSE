import tkinter as tk
from tkinter import filedialog, messagebox, Entry, Label, Button, Toplevel, Menu, ttk
import ttkbootstrap as ttkbs
from ttkbootstrap.constants import *
import base64
import json
import os
import shutil
import subprocess
import platform
import re


class CloudMeadowSaveEditor:
    def __init__(self, master):
        self.master = master
        self.style = ttkbs.Style('flatly')
        self.master.geometry("800x450")
        self.master.minsize(800, 450)

        self.current_language = "en"

        self.translations = {
            "en": {
                # Menu
                "menu_file":     "File",
                "menu_open":     "Open",
                "menu_save":     "Save",
                "menu_exit":     "Exit",
                "menu_language": "Language",
                "menu_english":  "English",
                "menu_russian":  "Russian",

                # Buttons (top toolbar)
                "btn_open":       "Open Save",
                "btn_save":       "Save Changes",
                "btn_restore":    "Restore Backup",
                "btn_open_folder":"Open Folder",

                # Buttons (bottom toolbar)
                "btn_clone":      "Show Clone Values",
                "btn_expand_all": "Expand All",
                "btn_collapse_all":"Collapse All",

                # Table headers
                "table_key":   "Key",
                "table_value": "Value",

                # Titles, messages
                "title_main":        "Cloud Meadow Save Editor",
                "title_backup_restored": "Backup Restored",
                "msg_backup_restored":    "Backup restored successfully!",
                "msg_backup_not_found":   "No backup file found.",
                "msg_save_updated":       "Save file updated!",
                "msg_save_failed":        "Failed to save changes:\n",
                "msg_open_failed":        "Failed to open/decode file:\n",
                "msg_select_compare":     "Please select items to compare",
                "msg_no_shared_keys":     "No shared keys found among the selected items.",
                "title_clone_window":     "Clone Values Editor",
                "lbl_clone_title":        "Update Values for Shared Keys:",
                "btn_apply":             "Apply Changes",
                "btn_cancel":            "Cancel",
                "msg_values_updated":    "Values updated!",
                "msg_no_changes":        "No changes were made.",
            },

            "ru": {
                # Menu
                "menu_file":     "Файл",
                "menu_open":     "Открыть",
                "menu_save":     "Сохранить",
                "menu_exit":     "Выход",
                "menu_language": "Язык",
                "menu_english":  "Английский",
                "menu_russian":  "Русский",

                # Buttons (top toolbar)
                "btn_open":       "Открыть",
                "btn_save":       "Сохранить изменения",
                "btn_restore":    "Восстановить бэкап",
                "btn_open_folder":"Открыть папку",

                # Buttons (bottom toolbar)
                "btn_clone":      "Сравнить значения",
                "btn_expand_all": "Развернуть всё",
                "btn_collapse_all":"Свернуть всё",

                # Table headers
                "table_key":   "Ключ",
                "table_value": "Значение",

                # Titles, messages
                "title_main":        "Редактор сохранений Cloud Meadow",
                "title_backup_restored": "Бэкап восстановлен",
                "msg_backup_restored":    "Резервная копия успешно восстановлена!",
                "msg_backup_not_found":   "Файл резервной копии не найден.",
                "msg_save_updated":       "Файл сохранён!",
                "msg_save_failed":        "Не удалось сохранить изменения:\n",
                "msg_open_failed":        "Не удалось открыть/декодировать файл:\n",
                "msg_select_compare":     "Выберите элементы для сравнения",
                "msg_no_shared_keys":     "Общих ключей не найдено",
                "title_clone_window":     "Редактор клонирования",
                "lbl_clone_title":        "Обновить значения общих ключей:",
                "btn_apply":             "Применить",
                "btn_cancel":            "Отмена",
                "msg_values_updated":    "Значения обновлены!",
                "msg_no_changes":        "Изменений не внесено.",
            }
        }

        self.master.title(self.tr("title_main"))

        self.save_data = {}
        self.original_data = ""
        self.current_file = ""
        self.current_tree_path = []
        self.backup_file = ""
        self.selected_items = set()

        self.create_menu()
        self.create_widgets()
        self.setup_selection_bindings()

    def tr(self, key):
        """Утилита для перевода строки по ключу."""
        return self.translations[self.current_language].get(key, f"<{key}>")

    def set_language(self, lang):
        """Переключение языка интерфейса."""
        self.current_language = lang
        self.master.title(self.tr("title_main"))
        self.apply_translations()

    def apply_translations(self):
        """Обновить все надписи в интерфейсе на текущий язык."""
        self.open_button.config(text=self.tr("btn_open"))
        self.save_button.config(text=self.tr("btn_save"))
        self.restore_backup_button.config(text=self.tr("btn_restore"))
        self.save_folder_button.config(text=self.tr("btn_open_folder"))

        self.show_clone_values_button.config(text=self.tr("btn_clone"))
        self.expand_all_button.config(text=self.tr("btn_expand_all"))
        self.collapse_all_button.config(text=self.tr("btn_collapse_all"))

        # Заголовки таблицы
        self.save_table.heading("Key", text=self.tr("table_key"))
        self.save_table.heading("Value", text=self.tr("table_value"))

    def try_decode_json(self, raw_data):
        decode_variants = [
            ("utf-8", False),
            ("utf-16-le", False),
            ("utf-8", True),
            ("utf-16-le", True),
        ]

        for encoding, filter_ctrl in decode_variants:
            try:
                text = raw_data.decode(encoding, errors='replace')
                text = text.replace('\x00', '')

                if filter_ctrl:
                    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]+', '', text)

                return json.loads(text)
            except Exception:
                pass
        return None

    def open_save_file(self):
        file_path = filedialog.askopenfilename(
            title=self.tr("btn_open"),
            filetypes=[("Json files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "rb") as f:
                    encoded_data = f.read()

                try:
                    raw_data = base64.b64decode(encoded_data, validate=False)
                except Exception as e:
                    raise ValueError(f"Base64 decode error: {e}")

                data = self.try_decode_json(raw_data)
                if data is None:
                    raise ValueError("Cannot decode JSON in any known format")

                self.save_data = data
                self.original_data = raw_data
                self.current_file = file_path

                self.create_backup()
                self.update_gui_with_data()
                self.save_button.config(state="normal")
                self.restore_backup_button.config(state="normal")

            except Exception as e:
                messagebox.showerror(self.tr("menu_file"), 
                                     f"{self.tr('msg_open_failed')}{e}")

    def get_save_dir(self):
        try:
            return os.path.join(os.getenv('APPDATA'), '..', 'LocalLow', 'Team Nimbus', 'Cloud Meadow')
        except (TypeError, FileNotFoundError):
            try:
                return os.path.join(os.getenv('LOCALAPPDATA'), 'Team Nimbus', 'Cloud Meadow')
            except (TypeError, FileNotFoundError):
                return ""

    def create_menu(self):
        menubar = ttkbs.Menu(self.master)

        # Файл
        filemenu = ttkbs.Menu(menubar, tearoff=0)
        filemenu.add_command(label=self.tr("menu_open"), command=self.open_save_file)
        filemenu.add_command(label=self.tr("menu_save"), command=self.save_edits, state="disabled")
        filemenu.add_separator()
        filemenu.add_command(label=self.tr("menu_exit"), command=self.master.quit)
        menubar.add_cascade(label=self.tr("menu_file"), menu=filemenu)

        # Язык
        langmenu = ttkbs.Menu(menubar, tearoff=0)
        langmenu.add_command(label=self.tr("menu_english"), command=lambda: self.set_language("en"))
        langmenu.add_command(label=self.tr("menu_russian"), command=lambda: self.set_language("ru"))
        menubar.add_cascade(label=self.tr("menu_language"), menu=langmenu)

        self.master.config(menu=menubar)

    def create_widgets(self):
        top_toolbar = ttkbs.Frame(self.master, padding=(10, 5))
        top_toolbar.grid(row=0, column=0, columnspan=2, sticky='ew')

        bottom_toolbar = ttkbs.Frame(self.master, padding=(10, 5))
        bottom_toolbar.grid(row=2, column=0, columnspan=2, sticky='ew')

        self.open_button = ttkbs.Button(
            top_toolbar, text=self.tr("btn_open"), bootstyle="primary-outline",
            command=self.open_save_file
        )
        self.open_button.pack(side=tk.LEFT, padx=5)

        self.save_button = ttkbs.Button(
            top_toolbar, text=self.tr("btn_save"), bootstyle="success-outline",
            command=self.save_edits, state="disabled"
        )
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.restore_backup_button = ttkbs.Button(
            top_toolbar, text=self.tr("btn_restore"), bootstyle="warning-outline",
            command=self.restore_backup, state="disabled"
        )
        self.restore_backup_button.pack(side=tk.LEFT, padx=5)

        self.save_folder_button = ttkbs.Button(
            top_toolbar, text=self.tr("btn_open_folder"), bootstyle="info-outline",
            command=self.open_save_folder
        )
        self.save_folder_button.pack(side=tk.LEFT, padx=5)

        self.show_clone_values_button = ttkbs.Button(
            bottom_toolbar, text=self.tr("btn_clone"), bootstyle="info-outline",
            command=self.show_clone_values
        )
        self.show_clone_values_button.pack(side=tk.LEFT, padx=5)

        self.expand_all_button = ttkbs.Button(
            bottom_toolbar, text=self.tr("btn_expand_all"), width=14,
            bootstyle="info-outline", command=self.expand_all
        )
        self.expand_all_button.pack(side=tk.LEFT, padx=5)

        self.collapse_all_button = ttkbs.Button(
            bottom_toolbar, text=self.tr("btn_collapse_all"), width=14,
            bootstyle="info-outline", command=self.collapse_all
        )
        self.collapse_all_button.pack(side=tk.LEFT, padx=5)

        self.save_table = ttkbs.Treeview(
            self.master, columns=("Key", "Value"), show="headings", bootstyle=INFO
        )
        self.save_table.heading("Key", text=self.tr("table_key"))
        self.save_table.heading("Value", text=self.tr("table_value"))
        self.save_table.column("Key", width=300)
        self.save_table.column("Value", width=300)
        self.save_table.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.save_table.tag_configure("selected_tree", background=self.style.colors.info)
        self.save_table.tag_configure("error_tree", background=self.style.colors.danger)

        self.save_table.bind("<Double-1>", self.edit_value)
        self.save_table.bind("<Button-3>", self.show_context_menu)

        self.master.rowconfigure(1, weight=1)
        self.master.columnconfigure(0, weight=1)

    def open_save_folder(self):
        save_folder = self.get_save_dir()

        if not save_folder:
            messagebox.showwarning(self.tr("menu_file"), 
                                   "Could not auto-detect folder. Select manually.")
            save_folder = filedialog.askdirectory(title="Select Cloud Meadow save folder")
            if not save_folder:
                return

        if save_folder:
            try:
                system = platform.system()
                if system == "Windows":
                    os.startfile(save_folder)
                elif system == "Darwin":
                    subprocess.Popen(["open", save_folder])
                else:
                    subprocess.Popen(["xdg-open", save_folder])
            except Exception as e:
                messagebox.showerror(self.tr("menu_file"), f"Failed to open folder:\n{e}")

    def save_edits(self):
        if not self.current_file:
            return

        try:
            json_data = json.dumps(self.save_data, separators=(',', ':'))
            new_data = '\x00'.join(char for char in json_data)
            if not new_data.endswith('\x00'):
                new_data += '\x00'

            encoded_data = base64.b64encode(new_data.encode('utf-8'))

            with open(self.current_file, 'wb') as f:
                f.write(encoded_data)

            messagebox.showinfo(self.tr("menu_file"), self.tr("msg_save_updated"))

        except Exception as e:
            messagebox.showerror(self.tr("menu_file"), f"{self.tr('msg_save_failed')}{e}")

    def setup_selection_bindings(self):
        self.save_table.bind('<Button-1>', self.on_click)
        self.save_table.bind('<Control-Button-1>', self.on_ctrl_click)
        self.save_table.bind('<Button-3>', self.show_context_menu)

        style = ttk.Style()
        style.configure(
            "Treeview",
            rowheight=25,
            selectbackground='#e6e6e6',
            selectforeground='black'
        )

        self.save_table.tag_configure('custom_select', background='#e6e6e6')

    def show_context_menu(self, event):
        item = self.save_table.identify('item', event.x, event.y)
        if not item:
            return

        context_menu = tk.Menu(self.master, tearoff=0)
        context_menu.add_command(
            label="Select Heads Below",
            command=lambda: self.select_heads_below(item)
        )
        context_menu.post(event.x_root, event.y_root)

    def select_heads_below(self, parent_item):
        self.selected_items.clear()
        children = self.save_table.get_children(parent_item)

        for child in children:
            if self.save_table.get_children(child):
                self.selected_items.add(child)
                self.save_table.selection_add(child)

        self.update_selection()

    def update_selection(self):
        for item in self.save_table.get_children(''):
            self.clear_item_tags(item)
        self.save_table.selection_remove(self.save_table.selection())

        for item in self.selected_items:
            self.save_table.selection_add(item)

    def clear_item_tags(self, item):
        self.save_table.item(item, tags=())
        for child in self.save_table.get_children(item):
            self.clear_item_tags(child)

    def on_click(self, event):
        item = self.save_table.identify('item', event.x, event.y)
        if item:
            self.selected_items.clear()
            self.selected_items.add(item)
            self.update_selection()

    def on_ctrl_click(self, event):
        item = self.save_table.identify('item', event.x, event.y)
        if item:
            if item in self.selected_items:
                self.selected_items.remove(item)
            else:
                self.selected_items.add(item)
            self.update_selection()

        self.save_table.item(item, tags=())
        for child in self.save_table.get_children(item):
            self.clear_item_tags(child)

    def update_gui_with_data(self):
        for row in self.save_table.get_children():
            self.save_table.delete(row)

        def insert_data(data, parent="", indent="", can_expand=False):
            if isinstance(data, dict):
                for key, value in data.items():
                    prefix = "+ " if can_expand and (isinstance(value, dict) or isinstance(value, list)) else "  "
                    item = self.save_table.insert(parent, "end", values=(indent + prefix + key, ""))
                    self.save_table.item(item, open=False)
                    insert_data(value, item, indent + "   ", can_expand=True)
            elif isinstance(data, list):
                for i, value in enumerate(data):
                    prefix = "+ " if can_expand and (isinstance(value, dict) or isinstance(value, list)) else "  "
                    item = self.save_table.insert(parent, "end", values=(indent + prefix + f"[{i}]", ""))
                    self.save_table.item(item, open=False)
                    insert_data(value, item, indent + "   ", can_expand=True)
            else:
                self.save_table.item(parent, values=(self.save_table.item(parent)["values"][0], str(data)))

        insert_data(self.save_data)
        self.save_table.bind("<<TreeviewOpen>>", self.on_treeview_open)
        self.save_table.bind("<<TreeviewClose>>", self.on_treeview_close)
        self.save_table.bind("<<TreeviewSelect>>", self.on_treeview_select)

    def show_clone_values(self):
        selected_items = self.save_table.selection()
        if not selected_items:
            messagebox.showinfo(self.tr("menu_file"), self.tr("msg_select_compare"))
            return

        for item in selected_items:
            self.expand_item(item)

        paths = []
        selected_data = []

        for item in selected_items:
            path = self.get_item_key_path(item)
            paths.append(path)
            selected_data.append(self.fetch_data_by_path(path))

        shared_keys = self.find_shared_keys(selected_data)
        if not shared_keys:
            messagebox.showinfo(self.tr("menu_file"), self.tr("msg_no_shared_keys"))
            return

        clone_window = Toplevel(self.master)
        clone_window.title(self.tr("title_clone_window"))
        clone_window.geometry("800x600")

        Label(clone_window, text=self.tr("lbl_clone_title"), font=('Arial', 12, 'bold')).pack(pady=10)

        main_frame = ttk.Frame(clone_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        canvas = tk.Canvas(main_frame)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        v_scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar = ttk.Scrollbar(clone_window, orient=tk.HORIZONTAL, command=canvas.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        scrollable_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')

        new_values = {}

        for key in shared_keys:
            key_frame = ttk.Frame(scrollable_frame)
            key_frame.pack(fill=tk.X, pady=5, padx=5)

            key_label = ttk.Label(key_frame, text=str(key), width=20, anchor='w')
            key_label.pack(side=tk.LEFT, padx=(0, 10))

            current_values = [str(self.get_value_by_key(data, key)) for data in selected_data]
            values_text = "Current values: " + ", ".join(current_values)

            values_display = tk.Text(key_frame, height=2, width=40, wrap=tk.WORD)
            values_display.insert('1.0', values_text)
            values_display.configure(state='disabled')
            values_display.pack(side=tk.LEFT, padx=(0, 10))

            entry = ttk.Entry(key_frame, width=20)
            entry.pack(side=tk.LEFT)
            new_values[key] = entry

        button_frame = ttk.Frame(clone_window)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text=self.tr("btn_apply"),
                   command=lambda: self.apply_cloned_values(new_values, paths, clone_window)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text=self.tr("btn_cancel"),
                   command=clone_window.destroy).pack(side=tk.LEFT, padx=5)

        def update_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        scrollable_frame.bind('<Configure>', update_scroll_region)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all('<MouseWheel>', on_mousewheel)

    def apply_cloned_values(self, new_values, paths, window):
        changes_made = False
        for key, entry in new_values.items():
            value = entry.get().strip()
            if value:
                changes_made = True
                for path in paths:
                    self.batch_update_values(path, key, value)

        if changes_made:
            self.update_gui_with_data()
            messagebox.showinfo(self.tr("menu_file"), self.tr("msg_values_updated"))
            window.destroy()
        else:
            messagebox.showinfo(self.tr("menu_file"), self.tr("msg_no_changes"))

    def expand_item(self, item):
        children = self.save_table.get_children(item)
        if children:
            self.save_table.item(item, open=True)
            for child in children:
                self.expand_item(child)

    def find_shared_keys(self, data_list):
        if not data_list:
            return set()

        first = data_list[0]
        if isinstance(first, dict):
            shared = set(first.keys())
            for data in data_list[1:]:
                if not isinstance(data, dict):
                    return set()
                shared.intersection_update(data.keys())
            return shared
        elif isinstance(first, list):
            shared = set(range(len(first)))
            for data in data_list[1:]:
                if not isinstance(data, list) or len(data) != len(first):
                    return set()
                shared.intersection_update(range(len(data)))
            return shared

        return set()

    def get_value_by_key(self, data, key):
        try:
            return data[key]
        except (KeyError, IndexError, TypeError):
            return "N/A"

    def batch_update_values(self, path, key, new_value):
        data = self.fetch_data_by_path(path)
        if isinstance(data, dict):
            if key in data:
                try:
                    current_value = data[key]
                    if isinstance(current_value, bool):
                        new_value = (new_value.lower() == 'true')
                    elif isinstance(current_value, int):
                        new_value = int(new_value)
                    elif isinstance(current_value, float):
                        new_value = float(new_value)
                    data[key] = new_value
                except (ValueError, TypeError):
                    data[key] = new_value
            for k, v in data.items():
                if isinstance(v, (dict, list)):
                    self.batch_update_values(path + [k], key, new_value)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    self.batch_update_values(path + [str(i)], key, new_value)

    def fetch_data_by_path(self, path):
        obj = self.save_data
        for key in path:
            if isinstance(obj, list):
                key = int(key.strip("[]"))
            else:
                key = key.strip("+ -")
            obj = obj[key]
        return obj

    def collapse_all(self):
        for item in self.save_table.get_children():
            self.save_table.item(item, open=False)
            self.recursive_collapse(item)

    def expand_all(self):
        for item in self.save_table.get_children():
            self.save_table.item(item, open=True)
            self.recursive_expand(item)

    def recursive_collapse(self, item):
        for child in self.save_table.get_children(item):
            self.save_table.item(child, open=False)
            self.recursive_collapse(child)

    def recursive_expand(self, item):
        for child in self.save_table.get_children(item):
            self.save_table.item(child, open=True)
            self.recursive_expand(child)

    def on_treeview_open(self, event):
        item = self.save_table.selection()[0]
        self.update_tree_indicators(item, "open")

    def on_treeview_close(self, event):
        item = self.save_table.selection()[0]
        self.update_tree_indicators(item, "close")

    def update_tree_indicators(self, item, action):
        current_text = self.save_table.item(item, "values")[0]
        if action == "open" and "+ " in current_text:
            new_text = current_text.replace("+ ", "- ", 1)
            self.save_table.item(item, values=(new_text, self.save_table.item(item, "values")[1]))
        elif action == "close" and "- " in current_text:
            new_text = current_text.replace("- ", "+ ", 1)
            self.save_table.item(item, values=(new_text, self.save_table.item(item, "values")[1]))

    def on_treeview_select(self, event):
        try:
            item = self.save_table.selection()[0]
            for prev_item in self.current_tree_path:
                if self.save_table.exists(prev_item):
                    self.save_table.item(prev_item, tags="")

            self.current_tree_path = self.get_item_path(item)
            for tree_item in self.current_tree_path:
                self.save_table.item(tree_item, tags=("selected_tree"))
            self.save_table.tag_configure("selected_tree", background="#e0e0e0")
        except IndexError:
            pass

    def get_item_path(self, item):
        path = []
        while item:
            path.insert(0, item)
            item = self.save_table.parent(item)
        return path

    def edit_value(self, event):
        item = self.save_table.identify_row(event.y)
        if not item:
            return
        if self.save_table.get_children(item):
            return

        key_path = self.get_item_key_path(item)
        current_value = self.save_table.item(item, "values")[1]

        try:
            current_value = float(current_value)
            self.edit_text_value(item, key_path, current_value)
        except ValueError:
            if current_value.lower() in ["true", "false"]:
                self.toggle_boolean(item, key_path, current_value.lower() == "true")
            else:
                self.edit_text_value(item, key_path, current_value)

    def toggle_boolean(self, item, key_path, current_value):
        new_value = not current_value
        self.update_save_data_by_path(key_path, new_value)
        self.save_table.item(item, values=(self.save_table.item(item)["values"][0], str(new_value)))

    def edit_text_value(self, item, key_path, current_value):
        entry = tk.Entry(self.save_table)
        entry.insert(0, str(current_value))

        x, y, width, height = self.save_table.bbox(item, column="#2")
        entry.place(x=x, y=y, width=width, height=height)
        entry.focus_set()

        def save_and_close(event=None):
            new_value = entry.get()
            try:
                if isinstance(current_value, int):
                    new_value = int(new_value)
                elif isinstance(current_value, float):
                    new_value = float(new_value)
                elif isinstance(current_value, bool):
                    new_value = (new_value.lower() == "true")
                else:
                    new_value = str(new_value)

                self.update_save_data_by_path(key_path, new_value)
                self.save_table.set(item, column="#2", value=new_value)
            except ValueError as e:
                messagebox.showwarning(self.tr("menu_file"), f"Invalid input: {e}")
            finally:
                entry.destroy()

        entry.bind("<Return>", save_and_close)
        entry.bind("<FocusOut>", save_and_close)

    def update_save_data_by_path(self, key_path, new_value):
        obj = self.save_data
        for key in key_path[:-1]:
            if isinstance(obj, list):
                key = int(key.strip("[]"))
            else:
                key = key.strip()
            obj = obj[key]

        if isinstance(obj, list):
            obj[int(key_path[-1].strip("[]"))] = new_value
        else:
            obj[key_path[-1].strip()] = new_value

    def get_item_key_path(self, item):
        path = []
        while item:
            key = self.save_table.item(item, 'values')[0].strip("+ -")
            path.insert(0, key)
            item = self.save_table.parent(item)
        return path

    def create_backup(self):
        if self.current_file:
            self.backup_file = self.current_file + ".bak"
            shutil.copy2(self.current_file, self.backup_file)

    def restore_backup(self):
        if self.backup_file and os.path.exists(self.backup_file):
            try:
                shutil.copy2(self.backup_file, self.current_file)
                self.open_save_file()
                messagebox.showinfo(self.tr("menu_file"), self.tr("msg_backup_restored"))
            except Exception as e:
                messagebox.showerror(self.tr("menu_file"), f"Failed to restore backup:\n{e}")
        else:
            messagebox.showwarning(self.tr("menu_file"), self.tr("msg_backup_not_found"))

    def toggle_all_subitems(self, event):
        item = self.save_table.selection()[0]

        def recursive_expand(it):
            if self.save_table.get_children(it):
                self.save_table.item(it, open=True)
                for ch in self.save_table.get_children(it):
                    recursive_expand(ch)

        def recursive_close(it):
            if self.save_table.get_children(it):
                self.save_table.item(it, open=False)
                for ch in self.save_table.get_children(it):
                    recursive_close(ch)

        if not self.save_table.item(item, 'open'):
            recursive_expand(item)
        else:
            recursive_close(item)


if __name__ == "__main__":
    root = tk.Tk()
    app = CloudMeadowSaveEditor(root)
    root.mainloop()
