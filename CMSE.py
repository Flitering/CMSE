import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import base64
import json
import os
import shutil
import subprocess
import platform

class CloudMeadowSaveEditor:
    def __init__(self, master):
        self.master = master
        master.title("Cloud Meadow Save Editor")

        self.master = master
        master.title("Cloud Meadow Save Editor")
        master.style = ttk.Style()
        master.style.configure('TButton', font=('Helvetica', 10), padding=6, relief="flat")
        master.style.configure('TLabel', font=('Helvetica', 10))
        master.style.configure('Treeview.Heading', font=('Helvetica', 10, 'bold'))
        master.style.configure('Treeview', rowheight=25, font=('Helvetica', 10))

        # Adjust the Treeview style to have a cleaner look
        master.style.configure('Custom.Treeview', 
                               background='#ffffff', 
                               foreground='black', 
                               rowheight=25, 
                               fieldbackground='#ffffff',
                               bordercolor='gray', 
                               borderwidth=0)
        master.style.map('Custom.Treeview', 
                         background=[('selected', '#e0e0e0')])
        self.save_data = {}
        self.original_data = ""
        self.current_file = ""
        self.current_tree_path = []
        self.backup_file = ""

        self.create_menu()
        self.create_widgets()

    def open_save_file(self):
        file_path = filedialog.askopenfilename(
            initialdir=self.get_save_dir(),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "rb") as f:
                    encoded_data = f.read()
                decoded_data = base64.b64decode(encoded_data).decode("utf-8")
                json_data = ''.join(char for i, char in enumerate(decoded_data) if i % 2 == 0)

                self.original_data = decoded_data
                self.save_data = json.loads(json_data)
                self.current_file = file_path

                self.create_backup()
                self.update_gui_with_data()
                self.save_button.config(state="normal")
                self.restore_backup_button.config(state="normal")

            except (json.JSONDecodeError, Exception) as e:
                messagebox.showerror("Error", f"Failed to open/decode file:\n{e}")

    def get_save_dir(self):
        try:
            return os.path.join(os.getenv('APPDATA'), '..', 'LocalLow', 'Team Nimbus', 'Cloud Meadow')
        except (TypeError, FileNotFoundError):
            try:
                return os.path.join(os.getenv('LOCALAPPDATA'), 'Team Nimbus', 'Cloud Meadow')
            except (TypeError, FileNotFoundError):
                return ""

    def create_menu(self):
        menubar = tk.Menu(self.master)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open", command=self.open_save_file)
        filemenu.add_command(label="Save", command=self.save_edits, state="disabled")
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.master.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        self.master.config(menu=menubar)

    def create_widgets(self):
        self.open_button = ttk.Button(self.master, text="Open", command=self.open_save_file)
        self.open_button.grid(row=0, column=0, padx=10, pady=10)

        self.save_table = ttk.Treeview(self.master, columns=("Key", "Value"), show="headings")
        self.save_table.heading("Key", text="Key")
        self.save_table.heading("Value", text="Value")
        self.save_table.column("Key", width=300)
        self.save_table.column("Value", width=300)
        self.save_table.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.save_table.bind("<Double-1>", self.edit_value)

        self.save_table.tag_configure("selected_tree", background="#e0e0e0")

        self.master.rowconfigure(1, weight=1)
        self.master.columnconfigure(0, weight=1)

        self.save_button = ttk.Button(self.master, text="Save edits", command=self.save_edits, state="disabled")
        self.save_button.grid(row=2, column=1, pady=10)

        self.save_folder_button = ttk.Button(self.master, text="Open Save Folder", command=self.open_save_folder)
        self.save_folder_button.grid(row=0, column=1, padx=10, pady=10)

        self.restore_backup_button = ttk.Button(self.master, text="Restore Backup", command=self.restore_backup, state="disabled")
        self.restore_backup_button.grid(row=2, column=0, pady=10)

    def open_save_folder(self):
        save_folder = self.get_save_dir()

        if not save_folder:
            messagebox.showwarning("Folder Not Found", "Could not auto-detect save folder. Please select manually.")
            save_folder = filedialog.askdirectory(title="Select 'Cloud Meadow' save folder")
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
                messagebox.showerror("Error", f"Failed to open folder:\n{e}")

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
            messagebox.showinfo("Success", "Save file updated!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save changes:\n{e}")

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
                    key = self.save_table.item(parent, "values")[0]
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
                if self.save_table.exists(prev_item):  # Check if item exists before clearing its selection
                    self.save_table.item(prev_item, tags="")  # Clear previous selection

            self.current_tree_path = self.get_item_path(item)

            for tree_item in self.current_tree_path:
                self.save_table.item(tree_item, tags=("selected_tree"))
            self.save_table.tag_configure("selected_tree", background="#e0e0e0")
        except IndexError:
            pass  # Handle the case where item selection fails without crashing

    def get_item_path(self, item):
        path = []
        while item:
            path.insert(0, item)
            item = self.save_table.parent(item)
        return path

    def edit_value(self, event):
        item = self.save_table.identify_row(event.y)
        if not item:
            return  # No item clicked

        if self.save_table.get_children(item):  # if children list is not empty it means parent node
            return  # Don't allow editing of parent value

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
                # Retain the type of current_value more accurately
                if isinstance(current_value, int):
                    new_value = int(new_value)  # Ensure integers are retained as integers
                elif isinstance(current_value, float):
                    new_value = float(new_value)
                elif isinstance(current_value, bool):
                    new_value = new_value.lower() == "true"
                else:
                    new_value = str(new_value)  # Default to string

                self.update_save_data_by_path(key_path, new_value)
                self.save_table.set(item, column="#2", value=new_value)
            except ValueError as e:
                messagebox.showwarning("Error", f"Invalid input: {e}")
            finally:
                entry.destroy()

        entry.bind("<Return>", save_and_close)
        entry.bind("<FocusOut>", save_and_close)

    def update_save_data_by_path(self, key_path, new_value):
        obj = self.save_data
        for key in key_path[:-1]:
            if isinstance(obj, list):
                key = int(key.strip("[]"))  # Convert list index to int
            obj = obj[key.strip() if isinstance(key, str) else key]  # Ensures proper key handling
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
                messagebox.showinfo("Backup Restored", "Backup restored successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to restore backup:\n{e}")
        else:
            messagebox.showwarning("Backup Not Found", "No backup file found.")

root = tk.Tk()
root.geometry("600x450")
root.minsize(600, 450)
app = CloudMeadowSaveEditor(root)
root.mainloop()