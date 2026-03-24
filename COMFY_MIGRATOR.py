import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import shutil
import os
import json
import threading
import time

class ComfyMigratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ComfyUI Storage Migrator Pro")
        self.root.geometry("550x420")
        self.root.resizable(False, False)

        # UI Styling
        self.font = ("Arial", 10)
        
        # Variables
        self.source_path = tk.StringVar()
        self.dest_path = tk.StringVar()
        self.delete_src_var = tk.BooleanVar()
        self.last_migration = None
        
        # Thread Control Flags
        self.is_paused = False
        self.is_canceled = False

        self.setup_ui()

    def setup_ui(self):
        # Source Selection
        tk.Label(self.root, text="Current ComfyUI Folder(e.g., C:\\Users\\PC\\Documents\\ComfyUI):", font=self.font).pack(anchor="w", padx=20, pady=(15, 0))
        src_frame = tk.Frame(self.root)
        src_frame.pack(fill="x", padx=20, pady=5)
        tk.Entry(src_frame, textvariable=self.source_path, width=50, font=self.font).pack(side="left")
        tk.Button(src_frame, text="Browse", command=self.browse_source).pack(side="right")

        # Destination Selection
        tk.Label(self.root, text="New Destination Folder (e.g., D:\\ComfyUI):", font=self.font).pack(anchor="w", padx=20, pady=(10, 0))
        dst_frame = tk.Frame(self.root)
        dst_frame.pack(fill="x", padx=20, pady=5)
        tk.Entry(dst_frame, textvariable=self.dest_path, width=50, font=self.font).pack(side="left")
        tk.Button(dst_frame, text="Browse", command=self.browse_dest).pack(side="right")

        # Delete Checkbox
        self.delete_src_chk = tk.Checkbutton(
            self.root, 
            text="Delete original folder after successful migration", 
            variable=self.delete_src_var, 
            font=("Arial", 10, "bold"), 
            fg="#D32F2F"
        )
        self.delete_src_chk.pack(anchor="w", padx=20, pady=(5, 0))

        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", padx=20, pady=(15, 5))

        # Status Label
        self.status_label = tk.Label(self.root, text="Ready", fg="blue", font=self.font)
        self.status_label.pack(pady=5)
        
        # Action Buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        self.migrate_btn = tk.Button(btn_frame, text="Start Migration", font=("Arial", 10, "bold"), bg="#4CAF50", fg="white", width=15, command=self.start_migration)
        self.migrate_btn.grid(row=0, column=0, padx=5, pady=5)

        self.undo_btn = tk.Button(btn_frame, text="Undo Last", font=("Arial", 10), bg="#9E9E9E", fg="white", width=12, state="disabled", command=self.start_undo)
        self.undo_btn.grid(row=0, column=1, padx=5, pady=5)

        self.pause_btn = tk.Button(btn_frame, text="Pause", font=("Arial", 10), bg="#FF9800", fg="white", width=10, state="disabled", command=self.toggle_pause)
        self.pause_btn.grid(row=1, column=0, padx=5, pady=5, sticky="e")

        self.cancel_btn = tk.Button(btn_frame, text="Cancel", font=("Arial", 10), bg="#F44336", fg="white", width=10, state="disabled", command=self.cancel_migration)
        self.cancel_btn.grid(row=1, column=1, padx=5, pady=5, sticky="w")


    def browse_source(self):
        folder = filedialog.askdirectory(title="Select Current ComfyUI Folder")
        if folder:
            self.source_path.set(folder)

    def browse_dest(self):
        folder = filedialog.askdirectory(title="Select New Destination Folder")
        if folder:
            self.dest_path.set(folder)

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_btn.config(text="Resume", bg="#2196F3")
            self.update_status("Paused. Click Resume to continue.", "orange")
        else:
            self.pause_btn.config(text="Pause", bg="#FF9800")
            self.update_status("Resuming copy...", "blue")

    def cancel_migration(self):
        if messagebox.askyesno("Confirm Cancel", "Are you sure you want to cancel? Any partially copied files will be deleted."):
            self.is_canceled = True
            self.is_paused = False 

    def start_migration(self):
        src = self.source_path.get().strip()
        dst = self.dest_path.get().strip()

        if not src or not dst:
            messagebox.showwarning("Missing Info", "Please select both source and destination folders.")
            return
        if not os.path.exists(src):
            messagebox.showerror("Error", "Source folder does not exist.")
            return
        if src.lower() == dst.lower():
            messagebox.showerror("Error", "Source and Destination cannot be the same.")
            return

        if self.delete_src_var.get():
            alert_msg = (
                "WARNING: You have selected to delete the original folder.\n\n"
                "If the migration is successful, the old folder will be permanently deleted to free up space, "
                "and the 'Undo' feature will be disabled.\n\n"
                "Do you want to proceed?"
            )
            if not messagebox.askyesno("Destructive Action Warning", alert_msg, icon='warning'):
                return

        self.is_paused = False
        self.is_canceled = False
        self.progress_var.set(0)
        self.pause_btn.config(text="Pause", bg="#FF9800")

        self.toggle_buttons(running=True)
        threading.Thread(target=self.run_migration, args=(src, dst), daemon=True).start()

    def run_migration(self, src, dst):
        final_dst = ""
        deleted_source = False
        
        try:
            if os.path.exists(dst) and os.listdir(dst):
                final_dst = os.path.join(dst, os.path.basename(src))
            else:
                final_dst = dst

            if os.path.exists(final_dst) and os.listdir(final_dst):
                 self.update_status("Error: Destination already contains files.", "red")
                 self.toggle_buttons(running=False, enable_undo=False)
                 return

            self.update_status("Calculating file sizes...", "orange")
            
            # 1. Custom Copy with Progress
            self.copy_tree_with_progress(src, final_dst)
            
            # 2. Update Configs
            self.update_status("Updating configuration files...", "orange")
            updated_files = self.update_config_files(final_dst)

            # 3. Delete Original Folder (If Checked)
            if self.delete_src_var.get() and not self.is_canceled:
                self.update_status("Deleting original folder to free up space...", "orange")
                try:
                    shutil.rmtree(src, ignore_errors=True)
                    deleted_source = True
                except Exception as e:
                    self.update_status(f"Could not fully delete source: {e}", "red")

            # 4. Save state for Undo
            if not deleted_source:
                self.last_migration = {'original_src': src, 'new_dst': final_dst}
                msg = f"Successfully copied to:\n{final_dst}\n\nConfig files updated:\n{', '.join(updated_files) if updated_files else 'None Found!'}"
            else:
                self.last_migration = None
                msg = f"Successfully moved to:\n{final_dst}\n\nConfig files updated:\n{', '.join(updated_files) if updated_files else 'None Found!'}\n\nOld folder deleted."

            self.update_status("Migration Complete!", "green")
            
            if not updated_files:
                messagebox.showwarning("Warning", "Migration finished, but no config files were found to update. You may be using a portable version.")
            else:
                messagebox.showinfo("Success", msg)

        except Exception as e:
            if str(e) == "CANCELED":
                self.update_status("Cleaning up canceled migration...", "red")
                if os.path.exists(final_dst):
                    shutil.rmtree(final_dst, ignore_errors=True)
                self.update_status("Migration canceled. Partial files removed.", "red")
                messagebox.showinfo("Canceled", "Migration was canceled and partial files were cleaned up.")
            else:
                self.update_status("An error occurred during migration.", "red")
                messagebox.showerror("Migration Error", str(e))
        finally:
            self.toggle_buttons(running=False, enable_undo=bool(self.last_migration))

    def copy_tree_with_progress(self, src, dst):
        total_bytes = 0
        files_to_copy = []

        for dirpath, _, filenames in os.walk(src):
            for f in filenames:
                src_file = os.path.join(dirpath, f)
                total_bytes += os.path.getsize(src_file)
                rel_path = os.path.relpath(src_file, src)
                dst_file = os.path.join(dst, rel_path)
                files_to_copy.append((src_file, dst_file))

        copied_bytes = 0
        self.root.after(0, lambda: self.status_label.config(text="Copying files...", fg="blue"))

        for src_file, dst_file in files_to_copy:
            while self.is_paused and not self.is_canceled:
                time.sleep(0.5)
            
            if self.is_canceled:
                raise Exception("CANCELED")

            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            shutil.copy2(src_file, dst_file)
            
            copied_bytes += os.path.getsize(src_file)
            if total_bytes > 0:
                progress_percent = (copied_bytes / total_bytes) * 100
                self.root.after(0, lambda p=progress_percent: self.progress_var.set(p))

    def start_undo(self):
        if not self.last_migration:
            return
            
        orig_src = self.last_migration['original_src']
        new_dst = self.last_migration['new_dst']

        if not os.path.exists(orig_src):
            messagebox.showerror("Cannot Undo", "Your original source folder no longer exists. Undo aborted.")
            return

        confirm = messagebox.askyesno("Confirm Undo", f"This will point configurations back to:\n{orig_src}\n\nAnd DELETE the copied folder at:\n{new_dst}\n\nProceed?")
        if confirm:
            self.toggle_buttons(running=True, is_undoing=True)
            threading.Thread(target=self.run_undo, args=(orig_src, new_dst), daemon=True).start()

    def run_undo(self, orig_src, new_dst):
        try:
            self.update_status("Reverting configuration files...", "orange")
            self.progress_var.set(0)
            
            self.update_config_files(orig_src)

            self.update_status("Deleting copied folder to free space...", "orange")
            if os.path.exists(new_dst):
                shutil.rmtree(new_dst, ignore_errors=True)
            
            self.last_migration = None
            self.update_status("Undo Complete. Restored to original state.", "green")
            messagebox.showinfo("Undo Successful", "Configurations reverted and copied folder deleted.")

        except Exception as e:
            self.update_status("An error occurred during Undo.", "red")
            messagebox.showerror("Undo Error", str(e))
        finally:
            self.toggle_buttons(running=False, enable_undo=False)

    def update_config_files(self, target_path):
        appdata = os.getenv('APPDATA')
        comfy_appdata_dir = os.path.join(appdata, 'ComfyUI')
        updated_files = []

        if not os.path.exists(comfy_appdata_dir):
            return updated_files

        # 1. Update YAML (Preserving Exact Indentation)
        yaml_path = os.path.join(comfy_appdata_dir, 'extra_models_config.yaml')
        if os.path.exists(yaml_path):
            formatted_yaml_path = target_path.replace("\\", "/")
            with open(yaml_path, 'r') as file:
                lines = file.readlines()
            
            yaml_changed = False
            with open(yaml_path, 'w') as file:
                for line in lines:
                    if line.lstrip().startswith('base_path:'):
                        indent = len(line) - len(line.lstrip())
                        file.write(' ' * indent + f'base_path: {formatted_yaml_path}\n')
                        yaml_changed = True
                    else:
                        file.write(line)
            
            if yaml_changed:
                updated_files.append("extra_models_config.yaml")

        # 2. Update JSON (Checking for correct casing)
        json_path = os.path.join(comfy_appdata_dir, 'config.json')
        if os.path.exists(json_path):
            formatted_json_path = target_path.replace("/", "\\")
            with open(json_path, 'r') as file:
                data = json.load(file)
            
            json_changed = False
            if "installPath" in data:
                data["installPath"] = formatted_json_path
                json_changed = True
            elif "InstallPath" in data:
                data["InstallPath"] = formatted_json_path
                json_changed = True
                
            with open(json_path, 'w') as file:
                json.dump(data, file, indent=2)
                
            if json_changed:
                updated_files.append("config.json")

        return updated_files

    def update_status(self, text, color):
        self.root.after(0, lambda: self.status_label.config(text=text, fg=color))

    def toggle_buttons(self, running=False, enable_undo=False, is_undoing=False):
        def update():
            if running:
                self.migrate_btn.config(state="disabled")
                self.undo_btn.config(state="disabled")
                self.delete_src_chk.config(state="disabled")
                if not is_undoing:
                    self.pause_btn.config(state="normal")
                    self.cancel_btn.config(state="normal")
            else:
                self.migrate_btn.config(state="normal")
                self.undo_btn.config(state="normal" if enable_undo else "disabled")
                self.delete_src_chk.config(state="normal")
                self.pause_btn.config(state="disabled")
                self.cancel_btn.config(state="disabled")
        self.root.after(0, update)

if __name__ == "__main__":
    root = tk.Tk()
    app = ComfyMigratorApp(root)
    root.mainloop()
