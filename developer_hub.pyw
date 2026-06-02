import os
import sys
import json
import threading
import subprocess
import shutil
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext

# Determine directories
current_dir = os.path.dirname(os.path.abspath(__file__))
version_file = os.path.join(current_dir, "version.json")
build_bat = os.path.join(current_dir, "build.bat")
settings_file = os.path.join(os.path.expanduser("~"), "Documents", "ReelScript", "settings.json")

class DeveloperHubApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ReelScript - Developer & Update Hub")
        self.root.geometry("750x800")
        self.root.configure(bg="#12181f")
        
        # Styling parameters
        self.colors = {
            "bg_dark": "#12181f",
            "card_bg": "#1a232c",
            "accent_blue": "#1b8adb",
            "accent_green": "#10b981",
            "accent_amber": "#f59e0b",
            "text_light": "#ffffff",
            "text_muted": "#abb2bf",
            "border": "#25313e",
            "terminal_bg": "#0b0f19",
            "terminal_fg": "#3b82f6"
        }
        
        # Load version data
        self.load_version_data()
        
        # Load cloud folder path
        self.cloud_dir = self.load_cloud_dir()
        
        # Build widgets
        self.create_widgets()
        self.log("🚀 Developer Hub initialized successfully.\nReady to build and deploy.")

    def load_version_data(self):
        self.version_data = {"version": "2.5", "last_updated": "2026-05-31", "changelog": []}
        if os.path.exists(version_file):
            try:
                with open(version_file, "r", encoding="utf-8") as f:
                    self.version_data = json.load(f)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load version.json: {str(e)}")
        else:
            self.save_version_data()

    def save_version_data(self):
        try:
            with open(version_file, "w", encoding="utf-8") as f:
                json.dump(self.version_data, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save version.json: {str(e)}")

    def load_cloud_dir(self):
        default_path = r"G:\My Drive\scripts\ReelScript"
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r") as f:
                    settings = json.load(f)
                    val = settings.get("cloudDir")
                    return val if val else default_path
            except:
                pass
        return default_path

    def create_widgets(self):
        # Master Layout Padded Frame
        self.main_frame = tk.Frame(self.root, bg=self.colors["bg_dark"], padx=20, pady=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. HEADER SECTION
        self.header_frame = tk.Frame(self.main_frame, bg=self.colors["bg_dark"])
        self.header_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.title_icon = tk.Label(self.header_frame, text="☁️", font=("Segoe UI", 28), bg=self.colors["bg_dark"], fg=self.colors["accent_blue"])
        self.title_icon.pack(side=tk.LEFT, padx=(0, 10))
        
        self.title_label = tk.Label(
            self.header_frame, 
            text="ReelScript Developer Hub", 
            font=("Segoe UI", 18, "bold"), 
            bg=self.colors["bg_dark"], 
            fg=self.colors["text_light"]
        )
        self.title_label.pack(side=tk.LEFT, anchor=tk.W)
        
        self.subtitle_label = tk.Label(
            self.main_frame, 
            text="Manage version releases, write changelogs, build PyInstaller executables, and deploy updates to the cloud.", 
            font=("Segoe UI", 9), 
            bg=self.colors["bg_dark"], 
            fg=self.colors["text_muted"]
        )
        self.subtitle_label.pack(fill=tk.X, anchor=tk.W, pady=(0, 15))

        # 2. VERSION & CHANGELOG CARD
        self.card = tk.LabelFrame(
            self.main_frame, 
            text=" 📦 Release Manager ", 
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["card_bg"], 
            fg=self.colors["accent_blue"],
            bd=1, 
            relief=tk.SOLID, 
            padx=15, 
            pady=15
        )
        self.card.pack(fill=tk.BOTH, pady=(0, 15))

        # Version Row
        self.ver_frame = tk.Frame(self.card, bg=self.colors["card_bg"])
        self.ver_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.ver_label = tk.Label(self.ver_frame, text="Version Number:", font=("Segoe UI", 10), bg=self.colors["card_bg"], fg=self.colors["text_light"])
        self.ver_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.ver_entry = tk.Entry(
            self.ver_frame, 
            font=("Segoe UI", 10, "bold"), 
            bg=self.colors["bg_dark"], 
            fg=self.colors["text_light"],
            insertbackground="white",
            bd=1,
            relief=tk.SOLID,
            width=10
        )
        self.ver_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.ver_entry.insert(0, self.version_data["version"])
        
        # Increment buttons
        self.btn_patch = tk.Button(self.ver_frame, text="+0.0.1 (Patch)", font=("Segoe UI", 8), bg=self.colors["bg_dark"], fg=self.colors["accent_blue"], activebackground=self.colors["accent_blue"], activeforeground="white", bd=0, padx=6, pady=2, cursor="hand2", command=lambda: self.increment_version(0, 0, 1))
        self.btn_patch.pack(side=tk.LEFT, padx=3)
        
        self.btn_minor = tk.Button(self.ver_frame, text="+0.1 (Minor)", font=("Segoe UI", 8), bg=self.colors["bg_dark"], fg=self.colors["accent_blue"], activebackground=self.colors["accent_blue"], activeforeground="white", bd=0, padx=6, pady=2, cursor="hand2", command=lambda: self.increment_version(0, 1, 0))
        self.btn_minor.pack(side=tk.LEFT, padx=3)

        self.btn_major = tk.Button(self.ver_frame, text="+1.0 (Major)", font=("Segoe UI", 8), bg=self.colors["bg_dark"], fg=self.colors["accent_blue"], activebackground=self.colors["accent_blue"], activeforeground="white", bd=0, padx=6, pady=2, cursor="hand2", command=lambda: self.increment_version(1, 0, 0))
        self.btn_major.pack(side=tk.LEFT, padx=3)

        # Changelog area
        self.change_label = tk.Label(self.card, text="Changelog Updates (One point per line):", font=("Segoe UI", 10), bg=self.colors["card_bg"], fg=self.colors["text_light"])
        self.change_label.pack(anchor=tk.W, pady=(5, 5))
        
        self.change_text = tk.Text(
            self.card, 
            height=6, 
            font=("Segoe UI", 10), 
            bg=self.colors["bg_dark"], 
            fg=self.colors["text_light"],
            insertbackground="white",
            bd=1,
            relief=tk.SOLID
        )
        self.change_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.change_text.insert(tk.END, "\n".join(self.version_data["changelog"]))

        # Update button
        self.btn_update = tk.Button(
            self.card, 
            text="💾 Save & Update version.json", 
            font=("Segoe UI", 10, "bold"), 
            bg=self.colors["accent_blue"], 
            fg=self.colors["text_light"],
            activebackground="#1466a3",
            activeforeground="white",
            bd=0, 
            pady=6,
            cursor="hand2",
            command=self.save_and_update
        )
        self.btn_update.pack(fill=tk.X)

        # 3. CONTROL CARD & CLOUD DIR SETUP
        self.control_frame = tk.Frame(self.main_frame, bg=self.colors["bg_dark"])
        self.control_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Cloud folder row
        self.cloud_frame = tk.Frame(self.control_frame, bg=self.colors["bg_dark"])
        self.cloud_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.cloud_label = tk.Label(self.cloud_frame, text="Google Drive Deployment Target Folder:", font=("Segoe UI", 9, "bold"), bg=self.colors["bg_dark"], fg=self.colors["text_light"])
        self.cloud_label.pack(side=tk.LEFT)
        
        self.cloud_val = tk.Label(
            self.cloud_frame, 
            text=self.cloud_dir if self.cloud_dir else "Not set. Click 'Browse' to set path...", 
            font=("Segoe UI", 9, "italic"), 
            bg=self.colors["bg_dark"], 
            fg=self.colors["accent_amber"] if not self.cloud_dir else self.colors["accent_green"]
        )
        self.cloud_val.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        self.btn_browse = tk.Button(
            self.cloud_frame, 
            text="Browse...", 
            font=("Segoe UI", 8), 
            bg="#27313c", 
            fg=self.colors["text_light"],
            bd=0, 
            padx=10, 
            pady=3,
            cursor="hand2",
            command=self.browse_cloud_dir
        )
        self.btn_browse.pack(side=tk.RIGHT)

        # Main Hub Actions
        self.actions_grid = tk.Frame(self.control_frame, bg=self.colors["bg_dark"])
        self.actions_grid.pack(fill=tk.X)
        
        self.btn_build = tk.Button(
            self.actions_grid,
            text="🔨 Build Executable (build.bat)",
            font=("Segoe UI", 10, "bold"),
            bg="#27313c",
            fg=self.colors["text_light"],
            activebackground="#36424e",
            activeforeground="white",
            bd=0,
            pady=10,
            cursor="hand2",
            command=self.start_build
        )
        self.btn_build.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        self.btn_deploy = tk.Button(
            self.actions_grid,
            text="🚀 Deploy everything to Google Drive",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["accent_green"],
            fg=self.colors["text_light"],
            activebackground="#0e9f6e",
            activeforeground="white",
            bd=0,
            pady=10,
            cursor="hand2",
            command=self.deploy_to_cloud
        )
        self.btn_deploy.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # 4. TERMINAL LOG SECTION
        self.term_frame = tk.Frame(self.main_frame, bg=self.colors["bg_dark"])
        self.term_frame.pack(fill=tk.BOTH, expand=True)
        
        self.term_label = tk.Label(self.term_frame, text="Activity Logs:", font=("Segoe UI", 9, "bold"), bg=self.colors["bg_dark"], fg=self.colors["text_muted"])
        self.term_label.pack(anchor=tk.W, pady=(5, 5))

        self.terminal = scrolledtext.ScrolledText(
            self.term_frame,
            font=("Consolas", 9),
            bg=self.colors["terminal_bg"],
            fg="#22c55e",  # Classic bright green console output
            insertbackground="white",
            bd=1,
            relief=tk.SOLID
        )
        self.terminal.pack(fill=tk.BOTH, expand=True)

    def log(self, msg):
        self.terminal.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.terminal.see(tk.END)

    def increment_version(self, major, minor, patch):
        try:
            parts = self.ver_entry.get().split('.')
            while len(parts) < 3:
                parts.append('0')
            
            p_major = int(parts[0])
            p_minor = int(parts[1])
            p_patch = int(parts[2])
            
            if major > 0:
                p_major += major
                p_minor = 0
                p_patch = 0
            elif minor > 0:
                p_minor += minor
                p_patch = 0
            elif patch > 0:
                p_patch += patch
                
            new_ver = f"{p_major}.{p_minor}.{p_patch}"
            self.ver_entry.delete(0, tk.END)
            self.ver_entry.insert(0, new_ver)
            self.log(f"Version bumped to: {new_ver}")
        except ValueError:
            messagebox.showerror("Error", "Please make sure version fits format e.g. '2.5' or '2.5.0'")

    def browse_cloud_dir(self):
        dir_path = filedialog.askdirectory(title="Select Shared Google Drive Folder")
        if dir_path:
            self.cloud_dir = dir_path
            self.cloud_val.configure(text=dir_path, fg=self.colors["accent_green"])
            self.log(f"Set cloud directory destination: {dir_path}")
            
            # Save in settings.json to sync with ReelScript!
            try:
                os.makedirs(os.path.dirname(settings_file), exist_ok=True)
                settings = {}
                if os.path.exists(settings_file):
                    with open(settings_file, "r") as f:
                        settings = json.load(f)
                settings["cloudDir"] = dir_path
                with open(settings_file, "w") as f:
                    json.dump(settings, f, indent=4)
                self.log("Saved cloudDir path to settings.json.")
            except Exception as e:
                self.log(f"Warning: Failed to write cloudDir to settings.json: {str(e)}")

    def save_and_update(self):
        new_ver = self.ver_entry.get().strip()
        if not new_ver:
            messagebox.showerror("Error", "Version cannot be empty!")
            return
            
        changes = [line.strip() for line in self.change_text.get("1.0", tk.END).split("\n") if line.strip()]
        
        self.version_data["version"] = new_ver
        self.version_data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        self.version_data["changelog"] = changes
        
        self.save_version_data()
        self.log(f"💾 Updated release details in version.json (Version: {new_ver})")
        messagebox.showinfo("Success", f"version.json updated successfully to v{new_ver}!")

    def start_build(self):
        # Disable buttons during active operation to prevent collisions
        self.btn_build.configure(state=tk.DISABLED, bg="#2d3748")
        self.btn_deploy.configure(state=tk.DISABLED, bg="#2d3748")
        self.log("🛠️ Starting compilation pipeline...")
        
        # Start PyInstaller compilation in a non-blocking background thread
        threading.Thread(target=self.run_build_thread, daemon=True).start()

    def run_build_thread(self):
        try:
            if not os.path.exists(build_bat):
                self.root.after(0, lambda: self.log("❌ Error: build.bat not found in directory!"))
                return

            self.root.after(0, lambda: self.log("🔨 Spawning compilation subprocess (pyinstaller)..."))
            
            creationflags = 0
            if os.name == 'nt':
                creationflags = 0x08000000  # CREATE_NO_WINDOW
                
            process = subprocess.Popen(
                [build_bat],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=creationflags,
                cwd=current_dir
            )

            # Stream build output to our GUI log console line by line
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                # Forward to main thread to safely update UI widget
                self.root.after(0, lambda l=line.strip(): self.terminal.insert(tk.END, f"   {l}\n"))
                self.root.after(0, lambda: self.terminal.see(tk.END))

            process.wait()
            
            if process.returncode == 0:
                self.root.after(0, lambda: self.log("✨ COMPILATION PIPELINE SUCCESSFUL!\nBinary built at dist/reelscript.exe"))
                self.root.after(0, lambda: messagebox.showinfo("Build Success", "ReelScript executable compiled successfully!"))
            else:
                self.root.after(0, lambda: self.log(f"❌ Error: Compilation failed with return code {process.returncode}"))
                self.root.after(0, lambda: messagebox.showerror("Build Failed", f"PyInstaller build failed with exit code {process.returncode}"))

        except Exception as e:
            self.root.after(0, lambda: self.log(f"❌ Subprocess Exception: {str(e)}"))
        finally:
            # Re-enable interactive buttons on main thread
            self.root.after(0, lambda: self.btn_build.configure(state=tk.NORMAL, bg="#27313c"))
            self.root.after(0, lambda: self.btn_deploy.configure(state=tk.NORMAL, bg=self.colors["accent_green"]))

    def deploy_to_cloud(self):
        if not self.cloud_dir:
            messagebox.showerror("Error", "Cloud deployment target folder is not configured!")
            return
            
        exe_path = os.path.join(current_dir, "dist", "reelscript.exe")
        if not os.path.exists(exe_path):
            messagebox.showerror("Error", "Compiled executable not found inside 'dist/' folder.\nPlease run 'Build Executable' first.")
            return

        self.log(f"🚀 Initializing cloud deployment to: {self.cloud_dir}")
        
        try:
            # Ensure target folder exists
            if not os.path.exists(self.cloud_dir):
                self.log(f"📁 Creating target cloud folder: {self.cloud_dir}")
                os.makedirs(self.cloud_dir, exist_ok=True)
                
            # 1. Copy Executable
            dest_exe = os.path.join(self.cloud_dir, "reelscript.exe")
            self.log(f"📤 Copying reelscript.exe to {dest_exe}...")
            shutil.copy2(exe_path, dest_exe)
            
            # 1b. Also update local C:\ReelScript installation if it exists
            local_install_dir = r"C:\ReelScript"
            if os.path.exists(local_install_dir):
                self.log("📤 Updating local installation at C:\\ReelScript...")
                try:
                    shutil.copy2(exe_path, os.path.join(local_install_dir, "ReelScript.exe"))
                    shutil.copy2(exe_path, os.path.join(local_install_dir, "reelscript.exe"))
                except Exception as ex:
                    self.log(f"   (Local C:\\ReelScript update skipped or file locked: {str(ex)})")
            
            # 2. Copy version.json
            dest_version = os.path.join(self.cloud_dir, "version.json")
            self.log(f"📤 Copying version.json to {dest_version}...")
            shutil.copy2(version_file, dest_version)
            
            # 2b. Also update version.json in C:\ReelScript if it exists
            if os.path.exists(local_install_dir):
                try:
                    shutil.copy2(version_file, os.path.join(local_install_dir, "version.json"))
                except Exception as ex:
                    pass
            
            self.log("✅ DEPLOYMENT PIPELINE COMPLETE!\nAll assets updated successfully on your Google Drive shared folder.")
            messagebox.showinfo("Deploy Success", f"ReelScript executable and version details successfully deployed to cloud!\n\nFolder: {self.cloud_dir}")
        except Exception as e:
            self.log(f"❌ Deploy Exception: {str(e)}")
            messagebox.showerror("Deploy Failed", f"An error occurred during deployment: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    # Dark Mode Window border styling on modern Windows
    try:
        import ctypes
        # Set dark-mode title bar if on Windows 10/11
        if os.name == 'nt':
            root.update()
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            set_imm_dark = ctypes.windll.dwmapi.DwmSetWindowAttribute
            hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
            set_imm_dark(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(ctypes.c_int(1)), 4)
    except:
        pass
        
    app = DeveloperHubApp(root)
    root.mainloop()
