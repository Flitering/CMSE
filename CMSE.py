import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import base64
import json
import os
import shutil

class CloudMeadowSaveEditor:
    def __init__(self, master):
        self.master = master
        master.title("Cloud Meadow Save Editor")

        self.save_data = {}
        self.original_data = ""
        self.current_file = ""
        self.current_tree_path = []
        self.backup_file = ""  # To store the backup file path

        self.create_menu()
        self.create_widgets()

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
        self.open_button = tk.Button(self.master, text="Open", command=self.open_save_file, width=10)
        self.open_button.grid(row=0, column=0, padx=10, pady=10)

        self.save_table = ttk.Treeview(self.master, columns=("Key", "Value"), show="headings")
        self.save_table.heading("Key", text="Key")
        self.save_table.heading("Value", text="Value")
        self.save_table.column("Key", width=300)
        self.save_table.column("Value", width=300)
        self.save_table.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.save_table.bind("<Double-1>", self.edit_value)

        self.master.rowconfigure(1, weight=1)
        self.master.columnconfigure(0, weight=1)
        self.master.columnconfigure(1, weight=1)

        self.save_button = tk.Button(self.master, text="Save edits", command=self.save_edits, state="disabled")
        self.save_button.grid(row=2, column=1, pady=10)

        self.save_folder_button = tk.Button(
            self.master, 
            text="Save Folder", 
            command=self.open_save_folder, 
            width=12 
        )
        self.save_folder_button.grid(row=0, column=1, padx=10, pady=10)

        # Restore Backup Button
        self.restore_backup_button = tk.Button(
            self.master, 
            text="Restore Backup", 
            command=self.restore_backup, 
            width=15,
            state="disabled"  
        )
        self.restore_backup_button.grid(row=2, column=0, pady=10)

    def open_save_file(self):
        file_path = filedialog.askopenfilename(
            initialdir=os.path.join(os.getenv('APPDATA'), '..', 'LocalLow', 'Team Nimbus', 'Cloud Meadow', '1'),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "rb") as f:
                    encoded_data = f.read()
                decoded_data = base64.b64decode(encoded_data).decode("utf-8")
                
                # Remove NUL characters while preserving the structure
                json_data = ''.join(char for i, char in enumerate(decoded_data) if i % 2 == 0)

                self.original_data = decoded_data
                self.save_data = json.loads(json_data)
                self.current_file = file_path
                
                # Create a backup
                self.create_backup()
                
                self.update_gui_with_data()
                self.save_button.config(state="normal")
                self.restore_backup_button.config(state="normal")  # Enable backup restore

            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file:\n{e}")

    def save_edits(self):
        if not self.current_file:
            return

        try:
            json_data = json.dumps(self.save_data, separators=(',', ':'))
            
            # Reinsert NUL characters
            new_data = '\x00'.join(char for char in json_data)
            
            # Add a NUL character at the end if it's not there
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
                    # Get the key from the parent for list items:
                    key = self.save_table.item(parent, "values")[0] 
                    prefix = "+ " if can_expand and (isinstance(value, dict) or isinstance(value, list)) else "  "
                    item = self.save_table.insert(parent, "end", values=(indent + prefix + f"[{i}]", ""))
                    self.save_table.item(item, open=False)
                    insert_data(value, item, indent + "   ", can_expand=True) 
            else:
                self.save_table.item(parent, values=(
                    self.save_table.item(parent)["values"][0], str(data)
                ))

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
        item = self.save_table.selection()[0]

        for prev_item in self.current_tree_path:
            self.save_table.item(prev_item, tags="")

        self.current_tree_path = self.get_item_path(item)

        for tree_item in self.current_tree_path:
            self.save_table.item(tree_item, tags=("selected_tree"))

        self.save_table.tag_configure("selected_tree", background="#e0e0e0")  

    def get_item_path(self, item):
        path = []
        while item:
            path.insert(0, item)
            item = self.save_table.parent(item)
        return path
        
    def edit_value(self, event):
        item = self.save_table.identify_row(event.y)
        column = self.save_table.identify_column(event.x)

        if not item or column != '#2':
            return

        key = self.save_table.item(item, "values")[0]
        current_value = self.save_table.item(item, "values")[1]

        entry = tk.Entry(self.save_table)
        entry.insert(0, str(current_value))

        x, y, width, height = self.save_table.bbox(item, column=column)
        entry.place(x=x, y=y, width=width, height=height)
        entry.focus_set()

        def save_and_close(event=None):
            new_value = entry.get()
            try:
                if isinstance(current_value, bool):
                    new_value = new_value.lower() == "true"
                elif isinstance(current_value, float):
                    new_value = float(new_value)
                elif isinstance(current_value, int):
                    new_value = int(new_value) 
                self.update_save_data_by_key(key, new_value) 

                self.save_table.set(item, column=column, value=new_value)
            except ValueError:
                messagebox.showwarning("Error", "Invalid value type.")
            finally:
                entry.destroy()

        entry.bind("<Return>", save_and_close)
        entry.bind("<FocusOut>", save_and_close)
        
    def update_save_data_by_key(self, display_key, new_value):
        actual_key = display_key.strip().replace("+ ", "").replace("- ", "")

        def update_nested_dict(data, target_key, value):
            if target_key in data:
                data[target_key] = value
                return True
            for k, v in data.items():
                if isinstance(v, dict) and update_nested_dict(v, target_key, value):
                    return True 
            return False

        update_nested_dict(self.save_data, actual_key, new_value)

    def open_save_folder(self):
        save_folder = os.path.join(os.getenv('APPDATA'), '..', 'LocalLow', 'Team Nimbus', 'Cloud Meadow', '1')
        if os.path.exists(save_folder):
            os.startfile(save_folder)  # Opens the folder in File Explorer
        else:
            messagebox.showwarning("Folder Not Found", 
                                   "The save folder was not found. It might be in a different location.")

    def create_backup(self):
        if self.current_file:
            self.backup_file = self.current_file + ".bak"
            shutil.copy2(self.current_file, self.backup_file) 

    def restore_backup(self):
        if self.backup_file and os.path.exists(self.backup_file):
            try:
                # Replace the current file with the backup
                shutil.copy2(self.backup_file, self.current_file)
                # Re-open the restored file to refresh the GUI
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
