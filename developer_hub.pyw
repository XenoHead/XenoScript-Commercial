import os
import sys
import json
import threading
import subprocess
import shutil
import re
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext, ttk
import requests
import random
import string

# Determine directories
current_dir = os.path.dirname(os.path.abspath(__file__))
version_file = os.path.join(current_dir, "version.json")
build_bat = os.path.join(current_dir, "build.bat")

# Determine settings file path dynamically (portable mode check)
use_portable = False
try:
    test_file = os.path.join(current_dir, ".write_test")
    with open(test_file, "w") as f:
        pass
    os.remove(test_file)
    use_portable = True
except (IOError, OSError, PermissionError):
    use_portable = False

if use_portable:
    settings_file = os.path.join(current_dir, "settings.json")
else:
    settings_file = os.path.join(os.path.expanduser("~"), "Documents", "XenoScript", "Backups", "settings.json")

class DeveloperHubApp:
    def __init__(self, root):
        self.root = root
        self.root.title("XenoScript - Developer & Update Hub")
        self.root.geometry("800x950")
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
        
        # Load Git info
        self.load_git_info()
        
        # Load GitHub Token
        self.github_token = self.load_github_token()
        
        # Build widgets
        self.create_widgets()
        self.log("🚀 Developer Hub initialized successfully.\nReady to build and deploy.")
        
        # Fetch registration keys automatically
        self.refresh_keys()

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

    def get_installed_version(self):
        installed_version = "Not Installed"
        install_path = None
        try:
            import winreg
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"Software\XenoHead\XenoScript", 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
            except OSError:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"Software\XenoHead\XenoScript", 0, winreg.KEY_READ | winreg.KEY_WOW64_32KEY)
            
            install_path, _ = winreg.QueryValueEx(key, "InstallPath")
            winreg.CloseKey(key)
        except Exception:
            # Fallback to default paths
            for p in [r"C:\Program Files\XenoScript", r"C:\Program Files (x86)\XenoScript", r"C:\XenoScript"]:
                if os.path.exists(os.path.join(p, "XenoScript.exe")) or os.path.exists(os.path.join(p, "xenoscript.exe")):
                    install_path = p
                    break
        
        if install_path and os.path.exists(os.path.join(install_path, "version.json")):
            try:
                with open(os.path.join(install_path, "version.json"), "r", encoding="utf-8") as f:
                    vdata = json.load(f)
                    installed_version = f"v{vdata.get('version', 'Unknown')} ({install_path})"
            except Exception:
                installed_version = f"Error reading version.json at {install_path}"
        elif install_path:
            installed_version = f"Unknown Version ({install_path})"
            
        return installed_version

    def load_github_token(self):
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r") as f:
                    settings = json.load(f)
                    return settings.get("githubToken", "")
            except:
                pass
        return ""

    def save_github_token(self, token):
        try:
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            settings = {}
            if os.path.exists(settings_file):
                with open(settings_file, "r") as f:
                    settings = json.load(f)
            settings["githubToken"] = token
            with open(settings_file, "w") as f:
                json.dump(settings, f, indent=4)
            self.github_token = token
        except Exception as e:
            self.log(f"Warning: Failed to save GitHub token to settings.json: {str(e)}")

    def load_git_info(self):
        self.git_repo = "Unknown Repository"
        self.git_branch = "Unknown Branch"
        try:
            # Parse .git/config directly to avoid invoking git executable (which crashes with 0xC0000005)
            config_path = os.path.join(current_dir, ".git", "config")
            if os.path.exists(config_path):
                in_origin = False
                with open(config_path, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('[remote "origin"]'):
                            in_origin = True
                        elif line.startswith('[') and in_origin:
                            in_origin = False
                        elif in_origin and line.startswith('url ='):
                            self.git_repo = line.split('url =', 1)[1].strip()
                            break
            
            # Parse .git/HEAD directly
            head_path = os.path.join(current_dir, ".git", "HEAD")
            if os.path.exists(head_path):
                with open(head_path, "r", encoding="utf-8", errors="replace") as f:
                    ref = f.read().strip()
                if ref.startswith("ref: refs/heads/"):
                    self.git_branch = ref.split("ref: refs/heads/", 1)[1].strip()
        except Exception as e:
            pass

    def refresh_git_info(self):
        self.load_git_info()
        git_display = f"{self.git_repo} (branch: {self.git_branch})"
        self.git_val.configure(text=git_display)
        self.log(f"Refreshed Git Info. Repo: {self.git_repo}, Branch: {self.git_branch}")

    def parse_github_url(self, url):
        match = re.search(r"github\.com[:/]([^/]+)/([^/.]+)(?:\.git)?", url)
        if match:
            return match.group(1), match.group(2)
        return None, None

    def create_widgets(self):
        # Master Layout Padded Frame
        self.main_frame = tk.Frame(self.root, bg=self.colors["bg_dark"], padx=20, pady=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. HEADER SECTION
        self.header_frame = tk.Frame(self.main_frame, bg=self.colors["bg_dark"])
        self.header_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.title_icon = tk.Label(self.header_frame, text="🚀", font=("Segoe UI", 28), bg=self.colors["bg_dark"], fg=self.colors["accent_blue"])
        self.title_icon.pack(side=tk.LEFT, padx=(0, 10))
        
        self.title_label = tk.Label(
            self.header_frame, 
            text="XenoScript Developer Hub", 
            font=("Segoe UI", 18, "bold"), 
            bg=self.colors["bg_dark"], 
            fg=self.colors["text_light"]
        )
        self.title_label.pack(side=tk.LEFT, anchor=tk.W)
        
        self.subtitle_label = tk.Label(
            self.main_frame, 
            text="Manage version releases, write changelogs, build PyInstaller executables, and push updates to GitHub.", 
            font=("Segoe UI", 9), 
            bg=self.colors["bg_dark"], 
            fg=self.colors["text_muted"]
        )
        self.subtitle_label.pack(fill=tk.X, anchor=tk.W, pady=(0, 15))

        # Style settings for TTK Notebook & Treeview
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background=self.colors["bg_dark"], borderwidth=0)
        style.configure('TNotebook.Tab', background=self.colors["card_bg"], foreground=self.colors["text_muted"], padding=[15, 5], font=("Segoe UI", 10))
        style.map('TNotebook.Tab', background=[('selected', self.colors["accent_blue"])], foreground=[('selected', self.colors["text_light"])])
        
        style.configure("RegKeys.Treeview", background=self.colors["card_bg"], fieldbackground=self.colors["card_bg"], foreground=self.colors["text_light"], borderwidth=0, font=("Segoe UI", 9))
        style.configure("RegKeys.Treeview.Heading", background=self.colors["bg_dark"], foreground=self.colors["text_muted"], font=("Segoe UI", 9, "bold"))

        # Notebook tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        self.tab_release = tk.Frame(self.notebook, bg=self.colors["bg_dark"])
        self.tab_regkeys = tk.Frame(self.notebook, bg=self.colors["bg_dark"], padx=10, pady=10)

        self.notebook.add(self.tab_release, text=" Release & Git ")
        self.notebook.add(self.tab_regkeys, text=" Reg Keys ")

        # 2. VERSION & CHANGELOG CARD (under tab_release)
        self.card = tk.LabelFrame(
            self.tab_release, 
            text=" 📦 Release Manager ", 
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["card_bg"], 
            fg=self.colors["accent_blue"],
            bd=1, 
            relief=tk.SOLID, 
            padx=15, 
            pady=15
        )
        self.card.pack(fill=tk.X, pady=(0, 15))

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

        # Installed Version Row
        self.inst_ver_frame = tk.Frame(self.card, bg=self.colors["card_bg"])
        self.inst_ver_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.inst_ver_title = tk.Label(self.inst_ver_frame, text="Locally Installed:", font=("Segoe UI", 9, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_muted"])
        self.inst_ver_title.pack(side=tk.LEFT, padx=(0, 5))
        
        self.inst_ver_label = tk.Label(self.inst_ver_frame, text=self.get_installed_version(), font=("Segoe UI", 9, "italic"), bg=self.colors["card_bg"], fg=self.colors["accent_amber"])
        self.inst_ver_label.pack(side=tk.LEFT)

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

        # 3. CONTROL CARD & GIT SETUP
        self.control_frame = tk.Frame(self.tab_release, bg=self.colors["bg_dark"])
        self.control_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Git repo row
        self.git_frame = tk.Frame(self.control_frame, bg=self.colors["bg_dark"])
        self.git_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.git_label = tk.Label(self.git_frame, text="GitHub Deployment Target:", font=("Segoe UI", 9, "bold"), bg=self.colors["bg_dark"], fg=self.colors["text_light"])
        self.git_label.pack(side=tk.LEFT)
        
        git_display = f"{self.git_repo} (branch: {self.git_branch})"
        self.git_val = tk.Label(
            self.git_frame, 
            text=git_display, 
            font=("Segoe UI", 9, "italic"), 
            bg=self.colors["bg_dark"], 
            fg=self.colors["accent_green"]
        )
        self.git_val.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        self.btn_refresh = tk.Button(
            self.git_frame, 
            text="Refresh Info", 
            font=("Segoe UI", 8), 
            bg="#27313c", 
            fg=self.colors["text_light"],
            bd=0, 
            padx=10, 
            pady=3,
            cursor="hand2",
            command=self.refresh_git_info
        )
        self.btn_refresh.pack(side=tk.RIGHT)

        # Git token row
        self.token_frame = tk.Frame(self.control_frame, bg=self.colors["bg_dark"])
        self.token_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.token_label = tk.Label(self.token_frame, text="GitHub Personal Access Token (PAT):", font=("Segoe UI", 9, "bold"), bg=self.colors["bg_dark"], fg=self.colors["text_light"])
        self.token_label.pack(side=tk.LEFT)
        
        self.token_entry = tk.Entry(
            self.token_frame,
            font=("Segoe UI", 9),
            bg=self.colors["card_bg"],
            fg=self.colors["text_light"],
            insertbackground="white",
            show="*",
            bd=1,
            relief=tk.SOLID,
            width=30
        )
        self.token_entry.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        self.token_entry.insert(0, self.github_token)
        self.token_entry.bind("<FocusOut>", lambda e: self.save_github_token(self.token_entry.get().strip()))

        def toggle_token_visibility():
            if self.token_entry.cget("show") == "*":
                self.token_entry.configure(show="")
                self.btn_show_token.configure(text="Hide")
            else:
                self.token_entry.configure(show="*")
                self.btn_show_token.configure(text="Show")

        self.btn_show_token = tk.Button(
            self.token_frame, 
            text="Show", 
            font=("Segoe UI", 8), 
            bg="#27313c", 
            fg=self.colors["text_light"],
            bd=0, 
            padx=10, 
            pady=3,
            cursor="hand2",
            command=toggle_token_visibility
        )
        self.btn_show_token.pack(side=tk.RIGHT)

        # Main Hub Actions
        self.actions_grid = tk.Frame(self.control_frame, bg=self.colors["bg_dark"])
        self.actions_grid.pack(fill=tk.X)
        
        # Build button spans full width on top
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
        self.btn_build.pack(fill=tk.X, pady=(0, 10))

        # Push Code Only & Push Release buttons side-by-side
        self.btn_push_code = tk.Button(
            self.actions_grid,
            text="💻 Git Push Code Only",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["accent_blue"],
            fg=self.colors["text_light"],
            activebackground="#1466a3",
            activeforeground="white",
            bd=0,
            pady=10,
            cursor="hand2",
            command=self.push_code_only
        )
        self.btn_push_code.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.btn_deploy = tk.Button(
            self.actions_grid,
            text="🚀 Push Release to GitHub",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["accent_green"],
            fg=self.colors["text_light"],
            activebackground="#0e9f6e",
            activeforeground="white",
            bd=0,
            pady=10,
            cursor="hand2",
            command=self.push_to_github
        )
        self.btn_deploy.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

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

        # --- TAB 2: REG KEYS ---
        # 1. Treeview to show all keys
        tree_frame = tk.Frame(self.tab_regkeys, bg=self.colors["bg_dark"])
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        scroll_y = tk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        cols = ("AutoKey", "AppName", "Authkey", "Regkey", "RegName", "RegEmail", "DateRegistered", "Active")
        self.tree = ttk.Treeview(
            tree_frame, 
            columns=cols, 
            show="headings", 
            yscrollcommand=scroll_y.set,
            style="RegKeys.Treeview"
        )
        scroll_y.config(command=self.tree.yview)

        col_configs = {
            "AutoKey": ("ID", 40, tk.CENTER),
            "AppName": ("App Name", 100, tk.W),
            "Authkey": ("Auth Key", 100, tk.W),
            "Regkey": ("Registration Key", 150, tk.W),
            "RegName": ("Name", 120, tk.W),
            "RegEmail": ("Email", 120, tk.W),
            "DateRegistered": ("Date Registered", 130, tk.W),
            "Active": ("Active", 50, tk.CENTER)
        }

        for col, config in col_configs.items():
            self.tree.heading(col, text=config[0], anchor=config[2])
            self.tree.column(col, width=config[1], minwidth=config[1], anchor=config[2])

        self.tree.pack(fill=tk.BOTH, expand=True)

        # 2. Control Buttons below Treeview
        reg_btn_frame = tk.Frame(self.tab_regkeys, bg=self.colors["bg_dark"])
        reg_btn_frame.pack(fill=tk.X, pady=5)

        self.btn_refresh_keys = tk.Button(
            reg_btn_frame, 
            text="🔄 Refresh Keys from D1", 
            font=("Segoe UI", 9, "bold"), 
            bg="#27313c", 
            fg=self.colors["text_light"],
            activebackground="#36424e",
            activeforeground="white",
            bd=0, 
            padx=15,
            pady=8,
            cursor="hand2",
            command=self.refresh_keys
        )
        self.btn_refresh_keys.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_add_key = tk.Button(
            reg_btn_frame, 
            text="➕ Generate & Add Key", 
            font=("Segoe UI", 9, "bold"), 
            bg=self.colors["accent_green"], 
            fg=self.colors["text_light"],
            activebackground="#0e9f6e",
            activeforeground="white",
            bd=0, 
            padx=15,
            pady=8,
            cursor="hand2",
            command=self.open_add_key_dialog
        )
        self.btn_add_key.pack(side=tk.LEFT)

        self.btn_edit_key = tk.Button(
            reg_btn_frame, 
            text="✏️ Edit Key", 
            font=("Segoe UI", 9, "bold"), 
            bg=self.colors["accent_blue"], 
            fg=self.colors["text_light"],
            activebackground="#1466a3",
            activeforeground="white",
            bd=0, 
            padx=15,
            pady=8,
            cursor="hand2",
            command=self.open_edit_key_dialog
        )
        self.btn_edit_key.pack(side=tk.LEFT, padx=10)

        # Context menu to copy registration key
        self.reg_menu = tk.Menu(self.root, tearoff=0, bg=self.colors["card_bg"], fg=self.colors["text_light"])
        self.reg_menu.add_command(label="Copy Registration Key", command=self.copy_selected_key)
        self.reg_menu.add_command(label="Edit Key Details", command=self.open_edit_key_dialog)
        self.tree.bind("<Button-3>", self.show_reg_context_menu)
        self.tree.bind("<Double-1>", lambda event: self.open_edit_key_dialog())

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

    def update_installer_iss_version(self, new_ver):
        iss_path = os.path.join(current_dir, "installer.iss")
        if os.path.exists(iss_path):
            try:
                with open(iss_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                updated = False
                for i, line in enumerate(lines):
                    # Look for #define AppVersion "..."
                    match = re.match(r'^#define\s+AppVersion\s+"[^"]+"', line)
                    if match:
                        eol = '\r\n' if line.endswith('\r\n') else '\n'
                        lines[i] = f'#define AppVersion     "{new_ver}"{eol}'
                        updated = True
                        break
                
                if updated:
                    with open(iss_path, "w", encoding="utf-8") as f:
                        f.writelines(lines)
                    self.log(f"📝 Updated version to {new_ver} in installer.iss")
                else:
                    self.log("⚠️ Warning: Could not find #define AppVersion line in installer.iss")
            except Exception as e:
                self.log(f"⚠️ Warning: Failed to update version in installer.iss: {str(e)}")
        else:
            self.log("ℹ️ installer.iss not found in directory. Skipping version update there.")

    def update_other_files_version(self, new_ver):
        # 1. Update xenoscript.pyw (DEFAULT_VERSION dict)
        pyw_path = os.path.join(current_dir, "xenoscript.pyw")
        if os.path.exists(pyw_path):
            try:
                with open(pyw_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                inside_default_version = False
                updated = False
                today_str = datetime.now().strftime("%Y-%m-%d")
                for i, line in enumerate(lines):
                    if "DEFAULT_VERSION = {" in line:
                        inside_default_version = True
                    if inside_default_version:
                        if '"version":' in line:
                            lines[i] = re.sub(r'"version":\s*"[^"]+"', f'"version": "{new_ver}"', line)
                            updated = True
                        elif '"last_updated":' in line:
                            lines[i] = re.sub(r'"last_updated":\s*"[^"]+"', f'"last_updated": "{today_str}"', line)
                        elif '}' in line:
                            inside_default_version = False
                            break
                
                if updated:
                    with open(pyw_path, "w", encoding="utf-8") as f:
                        f.writelines(lines)
                    self.log(f"📝 Updated DEFAULT_VERSION to {new_ver} in xenoscript.pyw")
            except Exception as e:
                self.log(f"⚠️ Warning: Failed to update version in xenoscript.pyw: {str(e)}")

        # 2. Update file_version_info.txt
        txt_path = os.path.join(current_dir, "file_version_info.txt")
        if os.path.exists(txt_path):
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Convert "4.5.7" -> "4, 5, 7, 0"
                ver_parts = new_ver.split(".")
                while len(ver_parts) < 4:
                    ver_parts.append("0")
                ver_tuple = ", ".join(ver_parts[:4])
                
                content = re.sub(r'filevers=\([^)]+\)', f'filevers=({ver_tuple})', content)
                content = re.sub(r'prodvers=\([^)]+\)', f'prodvers=({ver_tuple})', content)
                content = re.sub(r"u'FileVersion',\s*u'[^']+'", f"u'FileVersion', u'{new_ver}'", content)
                content = re.sub(r"u'ProductVersion',\s*u'[^']+'", f"u'ProductVersion', u'{new_ver}'", content)
                
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.log(f"📝 Updated version to {new_ver} in file_version_info.txt")
            except Exception as e:
                self.log(f"⚠️ Warning: Failed to update version in file_version_info.txt: {str(e)}")

        # 3. Update index.html
        html_path = os.path.join(current_dir, "index.html")
        if os.path.exists(html_path):
            try:
                with open(html_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                updated = False
                for i, line in enumerate(lines):
                    if 'id="about-version"' in line:
                        lines[i] = re.sub(r'id="about-version">[^<]+<', f'id="about-version">{new_ver}<', line)
                        updated = True
                        break
                
                if updated:
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.writelines(lines)
                    self.log(f"📝 Updated version to {new_ver} in index.html about modal")
            except Exception as e:
                self.log(f"⚠️ Warning: Failed to update version in index.html: {str(e)}")

        # 3. Update README.md
        readme_path = os.path.join(current_dir, "README.md")
        if os.path.exists(readme_path):
            try:
                with open(readme_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                updated = False
                today_pretty = datetime.now().strftime("%B %d, %Y")
                if today_pretty.split(" ")[1].startswith("0"):
                    today_pretty = today_pretty.replace(" 0", " ")
                
                for i, line in enumerate(lines):
                    if "**Current Version:**" in line:
                        line = re.sub(r'(\*\*Current Version:\*\*\s*)[^\s&]+', rf'\g<1>{new_ver}', line)
                        line = re.sub(r'(\*\*Last Updated:\*\*\s*)[^<\r\n]+', rf'\g<1>{today_pretty}', line)
                        lines[i] = line
                        updated = True
                        break
                
                if updated:
                    with open(readme_path, "w", encoding="utf-8") as f:
                        f.writelines(lines)
                    self.log(f"📝 Updated version to {new_ver} in README.md")
            except Exception as e:
                self.log(f"⚠️ Warning: Failed to update version in README.md: {str(e)}")

    def save_and_update_silent(self):
        new_ver = self.ver_entry.get().strip()
        if not new_ver:
            return False
            
        changes = [line.strip() for line in self.change_text.get("1.0", tk.END).split("\n") if line.strip()]
        
        self.version_data["version"] = new_ver
        self.version_data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        self.version_data["changelog"] = changes
        
        self.save_version_data()
        self.update_installer_iss_version(new_ver)
        self.update_other_files_version(new_ver)
        return True

    def save_and_update(self):
        if self.save_and_update_silent():
            new_ver = self.ver_entry.get().strip()
            self.log(f"💾 Updated release details in version.json and other source files (Version: {new_ver})")
            messagebox.showinfo("Success", f"version.json, installer.iss, and source files updated successfully to v{new_ver}!")
        else:
            messagebox.showerror("Error", "Version cannot be empty!")

    def _enable_buttons(self):
        try:
            self.btn_build.configure(state=tk.NORMAL, bg="#27313c")
            self.btn_push_code.configure(state=tk.NORMAL, bg=self.colors["accent_blue"])
            self.btn_deploy.configure(state=tk.NORMAL, bg=self.colors["accent_green"])
        except Exception as e:
            self.log(f"Error re-enabling buttons: {e}")

    def start_build(self):
        self.save_and_update_silent()
        # Disable buttons during active operation to prevent collisions
        self.btn_build.configure(state=tk.DISABLED, bg="#2d3748")
        self.btn_push_code.configure(state=tk.DISABLED, bg="#2d3748")
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
                encoding="utf-8",
                errors="replace",
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
                self.root.after(0, lambda: self.log("✨ COMPILATION PIPELINE SUCCESSFUL!\nBinary built at dist/xenoscript.exe"))
                self.root.after(0, lambda: messagebox.showinfo("Build Success", "XenoScript executable compiled successfully!"))
            else:
                self.root.after(0, lambda: self.log(f"❌ Error: Compilation failed with return code {process.returncode}"))
                self.root.after(0, lambda: messagebox.showerror("Build Failed", f"PyInstaller build failed with exit code {process.returncode}"))

        except Exception as e:
            self.root.after(0, lambda: self.log(f"❌ Subprocess Exception: {str(e)}"))
        finally:
            # Re-enable interactive buttons on main thread
            self.root.after(0, self._enable_buttons)

    def run_git_cmd(self, args):
        if not hasattr(self, "emulated_staged_files"):
            self.emulated_staged_files = {}
            self.emulated_commit_msg = ""
            self.emulated_tag = None
            self.emulated_tag_msg = ""

        cmd = args[0]
        subcmd = args[1] if len(args) > 1 else ""

        self.root.after(0, lambda: self.log(f"💻 [Emulated Git] Running: {' '.join(args)}"))

        if cmd == "git":
            if subcmd == "add":
                files_to_add = args[2:]
                if "-A" in files_to_add:
                    ignore_dirs = {".git", ".wrangler", "build", "dist", "Backups", "__pycache__"}
                    ignore_files = {"settings.json", "package-lock.json", "node_modules"}
                    
                    self.emulated_staged_files.clear()
                    for root, dirs, files in os.walk(current_dir):
                        dirs[:] = [d for d in dirs if d not in ignore_dirs]
                        for f in files:
                            if f in ignore_files or f.endswith((".pyc", ".pyo", ".spec")):
                                continue
                            abs_path = os.path.join(root, f)
                            rel_path = os.path.relpath(abs_path, current_dir).replace("\\", "/")
                            self.emulated_staged_files[rel_path] = abs_path
                    self.root.after(0, lambda: self.log(f"   Staged {len(self.emulated_staged_files)} files for commit."))
                    return 0, "Success"
                else:
                    for file_arg in files_to_add:
                        abs_path = os.path.abspath(os.path.join(current_dir, file_arg))
                        if os.path.exists(abs_path):
                            rel_path = os.path.relpath(abs_path, current_dir).replace("\\", "/")
                            self.emulated_staged_files[rel_path] = abs_path
                            self.root.after(0, lambda: self.log(f"   Staged file: {rel_path}"))
                        else:
                            self.root.after(0, lambda: self.log(f"   Warning: File not found: {file_arg}"))
                    return 0, "Success"

            elif subcmd == "commit":
                msg = ""
                for idx, arg in enumerate(args):
                    if (arg == "-m" or arg == "--message") and idx + 1 < len(args):
                        msg = args[idx + 1]
                        break
                self.emulated_commit_msg = msg
                self.root.after(0, lambda: self.log(f"   Committed changes with message: '{msg}'"))
                return 0, "Success"

            elif subcmd == "push":
                token = self.github_token or self.load_github_token()
                if not token:
                    self.root.after(0, lambda: self.log("   ❌ Error: GitHub PAT Token is missing in settings."))
                    return 1, "Error: GitHub PAT Token is missing"

                owner, repo = self.parse_github_url(self.git_repo)
                if not owner or not repo:
                    self.root.after(0, lambda: self.log(f"   ❌ Error: Could not parse owner/repo from {self.git_repo}"))
                    return 1, "Error: Could not parse owner/repo"

                branch = args[-1] if len(args) > 2 and args[-1] not in ("push", "origin") else self.git_branch
                if branch == "Unknown Branch" or not branch:
                    branch = "main"

                if len(args) > 3 and args[2] == "origin" and args[3].startswith("v"):
                    tag_name = args[3]
                    tag_res = self.emulate_create_tag_api(owner, repo, token, tag_name)
                    if tag_res:
                        return 0, "Success"
                    else:
                        return 1, "Tag creation failed"

                self.root.after(0, lambda: self.log(f"   Uploading staged changes to GitHub ({owner}/{repo} branch: {branch})..."))
                push_res = self.emulate_push_to_github_api(owner, repo, token, branch)
                if push_res:
                    self.emulated_staged_files.clear()
                    self.emulated_commit_msg = ""
                    return 0, "Success"
                else:
                    return 1, "Push failed"

            elif subcmd == "tag":
                tag_name = ""
                tag_msg = ""
                for idx, arg in enumerate(args):
                    if arg == "tag" and idx + 1 < len(args):
                        next_arg = args[idx+1]
                        if next_arg == "-a" and idx + 2 < len(args):
                            tag_name = args[idx+2]
                        else:
                            tag_name = next_arg
                    if (arg == "-m" or arg == "--message") and idx + 1 < len(args):
                        tag_msg = args[idx+1]
                
                self.emulated_tag = tag_name
                self.emulated_tag_msg = tag_msg
                self.root.after(0, lambda: self.log(f"   Tagged commit as {tag_name}"))
                return 0, "Success"

        return 1, f"Unknown command: {' '.join(args)}"

    def emulate_push_to_github_api(self, owner, repo, token, branch):
        import base64
        import requests

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json"
        }

        try:
            ref_url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{branch}"
            r_ref = requests.get(ref_url, headers=headers)
            
            latest_commit_sha = None
            base_tree_sha = None
            
            if r_ref.status_code == 200:
                ref_data = r_ref.json()
                latest_commit_sha = ref_data["object"]["sha"]
                self.root.after(0, lambda: self.log(f"   Latest commit SHA: {latest_commit_sha[:8]}"))

                commit_url = f"https://api.github.com/repos/{owner}/{repo}/git/commits/{latest_commit_sha}"
                r_commit = requests.get(commit_url, headers=headers)
                if r_commit.status_code == 200:
                    commit_data = r_commit.json()
                    base_tree_sha = commit_data["tree"]["sha"]
                    self.root.after(0, lambda: self.log(f"   Base tree SHA: {base_tree_sha[:8]}"))
                else:
                    self.root.after(0, lambda: self.log(f"   ❌ API Error getting latest commit: {r_commit.status_code} - {r_commit.text}"))
                    return False
            elif r_ref.status_code in (404, 409):
                self.root.after(0, lambda: self.log("   Empty or new branch detected. Creating initial commit..."))
            else:
                self.root.after(0, lambda: self.log(f"   ❌ API Error getting branch ref: {r_ref.status_code} - {r_ref.text}"))
                return False

            tree_nodes = []
            for rel_path, abs_path in self.emulated_staged_files.items():
                self.root.after(0, lambda r=rel_path: self.log(f"   Uploading blob for {r}..."))
                
                with open(abs_path, "rb") as f:
                    content_bytes = f.read()
                
                content_base64 = base64.b64encode(content_bytes).decode("utf-8")
                
                blob_data = {
                    "content": content_base64,
                    "encoding": "base64"
                }
                
                blob_url = f"https://api.github.com/repos/{owner}/{repo}/git/blobs"
                r_blob = requests.post(blob_url, headers=headers, json=blob_data)
                if r_blob.status_code not in (200, 201):
                    self.root.after(0, lambda r=rel_path: self.log(f"   ❌ API Error creating blob for {r}: {r_blob.status_code} - {r_blob.text}"))
                    return False
                
                blob_sha = r_blob.json()["sha"]
                tree_nodes.append({
                    "path": rel_path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_sha
                })

            if not tree_nodes:
                self.root.after(0, lambda: self.log("   No files staged/modified to push."))
                return True

            self.root.after(0, lambda: self.log("   Creating new Git tree on GitHub..."))
            tree_data = {
                "tree": tree_nodes
            }
            if base_tree_sha:
                tree_data["base_tree"] = base_tree_sha
                
            tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees"
            r_tree = requests.post(tree_url, headers=headers, json=tree_data)
            if r_tree.status_code not in (200, 201):
                self.root.after(0, lambda: self.log(f"   ❌ API Error creating tree: {r_tree.status_code} - {r_tree.text}"))
                return False
            
            new_tree_sha = r_tree.json()["sha"]
            self.root.after(0, lambda: self.log(f"   New tree SHA: {new_tree_sha[:8]}"))

            self.root.after(0, lambda: self.log("   Creating new Git commit on GitHub..."))
            commit_msg = self.emulated_commit_msg or "Update files (emulated commit)"
            new_commit_data = {
                "message": commit_msg,
                "tree": new_tree_sha,
                "parents": [latest_commit_sha] if latest_commit_sha else []
            }
            new_commit_url = f"https://api.github.com/repos/{owner}/{repo}/git/commits"
            r_new_commit = requests.post(new_commit_url, headers=headers, json=new_commit_data)
            if r_new_commit.status_code not in (200, 201):
                self.root.after(0, lambda: self.log(f"   ❌ API Error creating commit: {r_new_commit.status_code} - {r_new_commit.text}"))
                return False
            
            new_commit_sha = r_new_commit.json()["sha"]
            self.root.after(0, lambda: self.log(f"   New commit SHA: {new_commit_sha[:8]}"))

            if latest_commit_sha:
                self.root.after(0, lambda: self.log(f"   Updating reference refs/heads/{branch} to new commit..."))
                ref_update_data = {
                    "sha": new_commit_sha,
                    "force": False
                }
                ref_update_url = f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}"
                r_update = requests.patch(ref_update_url, headers=headers, json=ref_update_data)
            else:
                self.root.after(0, lambda: self.log(f"   Creating reference refs/heads/{branch} with new commit..."))
                ref_create_data = {
                    "ref": f"refs/heads/{branch}",
                    "sha": new_commit_sha
                }
                ref_create_url = f"https://api.github.com/repos/{owner}/{repo}/git/refs"
                r_update = requests.post(ref_create_url, headers=headers, json=ref_create_data)

            if r_update.status_code not in (200, 201):
                self.root.after(0, lambda: self.log(f"   ❌ API Error updating ref: {r_update.status_code} - {r_update.text}"))
                return False
            
            self.root.after(0, lambda: self.log("   ✅ Push completed successfully via GitHub API!"))
            return True

        except Exception as e:
            self.root.after(0, lambda: self.log(f"   ❌ Exception during emulated push: {str(e)}"))
            return False

    def emulate_create_tag_api(self, owner, repo, token, tag_name):
        import requests

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json"
        }

        try:
            branch = self.git_branch if self.git_branch != "Unknown Branch" else "main"
            ref_url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{branch}"
            r_ref = requests.get(ref_url, headers=headers)
            if r_ref.status_code != 200:
                self.root.after(0, lambda: self.log(f"   ❌ API Error getting branch ref: {r_ref.status_code} - {r_ref.text}"))
                return False
            
            commit_sha = r_ref.json()["object"]["sha"]

            self.root.after(0, lambda: self.log(f"   Creating tag object '{tag_name}' for commit {commit_sha[:8]}..."))
            tag_data = {
                "tag": tag_name,
                "message": self.emulated_tag_msg or f"Release {tag_name}",
                "object": commit_sha,
                "type": "commit"
            }
            tag_url = f"https://api.github.com/repos/{owner}/{repo}/git/tags"
            r_tag = requests.post(tag_url, headers=headers, json=tag_data)
            if r_tag.status_code not in (200, 201):
                self.root.after(0, lambda: self.log(f"   ❌ API Error creating tag object: {r_tag.status_code} - {r_tag.text}"))
                return False
            
            tag_obj_sha = r_tag.json()["sha"]

            self.root.after(0, lambda: self.log(f"   Publishing tag reference 'refs/tags/{tag_name}'..."))
            ref_data = {
                "ref": f"refs/tags/{tag_name}",
                "sha": tag_obj_sha
            }
            ref_url = f"https://api.github.com/repos/{owner}/{repo}/git/refs"
            r_ref_create = requests.post(ref_url, headers=headers, json=ref_data)
            if r_ref_create.status_code not in (200, 201):
                if r_ref_create.status_code == 422:
                    self.root.after(0, lambda: self.log(f"   Tag '{tag_name}' already exists. Updating reference..."))
                    update_ref_url = f"https://api.github.com/repos/{owner}/{repo}/git/refs/tags/{tag_name}"
                    ref_update_data = {
                        "sha": tag_obj_sha,
                        "force": True
                    }
                    r_ref_update = requests.patch(update_ref_url, headers=headers, json=ref_update_data)
                    if r_ref_update.status_code != 200:
                        self.root.after(0, lambda: self.log(f"   ❌ API Error updating tag ref: {r_ref_update.status_code} - {r_ref_update.text}"))
                        return False
                else:
                    self.root.after(0, lambda: self.log(f"   ❌ API Error creating tag ref: {r_ref_create.status_code} - {r_ref_create.text}"))
                    return False
            
            self.root.after(0, lambda: self.log(f"   ✅ Tag '{tag_name}' created successfully via GitHub API!"))
            return True

        except Exception as e:
            self.root.after(0, lambda: self.log(f"   ❌ Exception during tag creation: {str(e)}"))
            return False

    def push_code_only(self):
        self.save_and_update_silent()
        # Disable buttons during active operation to prevent collisions
        self.btn_build.configure(state=tk.DISABLED, bg="#2d3748")
        self.btn_push_code.configure(state=tk.DISABLED, bg="#2d3748")
        self.btn_deploy.configure(state=tk.DISABLED, bg="#2d3748")
        self.log("🚀 Starting Git push code pipeline...")
        
        # Start Git push in a non-blocking background thread
        threading.Thread(target=self.run_push_code_thread, daemon=True).start()

    def run_push_code_thread(self):
        try:
            # 1. Stage changes
            self.root.after(0, lambda: self.log("📂 Staging changes with git add..."))
            ret, out = self.run_git_cmd(["git", "add", "-A"])
            if ret != 0:
                self.root.after(0, lambda: self.log("❌ Error: git add failed!"))
                self.root.after(0, lambda: messagebox.showerror("Push Failed", "git add command failed."))
                return
            
            # 2. Commit changes
            new_ver = self.ver_entry.get().strip()
            changes = [line.strip() for line in self.change_text.get("1.0", tk.END).split("\n") if line.strip()]
            if changes:
                commit_msg = "Update: " + "; ".join(changes)
            else:
                commit_msg = f"Update code (v{new_ver})"
            
            self.root.after(0, lambda: self.log("💾 Committing changes with git commit..."))
            ret, out = self.run_git_cmd(["git", "commit", "-m", commit_msg])
            
            # If nothing to commit, that's fine, we can continue to push.
            if ret != 0 and "nothing to commit" not in out.lower() and "working tree clean" not in out.lower():
                self.root.after(0, lambda: self.log("❌ Error: git commit failed!"))
                self.root.after(0, lambda: messagebox.showerror("Push Failed", "git commit command failed."))
                return
            
            # 3. Push to remote
            branch = self.git_branch if self.git_branch != "Unknown Branch" else "main"
            self.root.after(0, lambda: self.log(f"📤 Pushing code to GitHub (origin/{branch})..."))
            ret, out = self.run_git_cmd(["git", "push", "origin", branch])
            if ret != 0:
                self.root.after(0, lambda: self.log("❌ Error: git push failed!"))
                self.root.after(0, lambda: messagebox.showerror("Push Failed", "git push command failed."))
                return
                
            self.root.after(0, lambda: self.log("✅ GIT PUSH CODE COMPLETE!\nChanges pushed successfully to GitHub."))
            self.root.after(0, lambda: messagebox.showinfo("Push Success", f"Changes successfully pushed to GitHub on branch '{branch}'!"))
            
        except Exception as e:
            self.root.after(0, lambda: self.log(f"❌ Push Exception: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("Push Failed", f"An error occurred during push: {str(e)}"))
        finally:
            self.root.after(0, self._enable_buttons)

    def push_to_github(self):
        self.save_and_update_silent()
        # Disable buttons during active operation to prevent collisions
        self.btn_build.configure(state=tk.DISABLED, bg="#2d3748")
        self.btn_push_code.configure(state=tk.DISABLED, bg="#2d3748")
        self.btn_deploy.configure(state=tk.DISABLED, bg="#2d3748")
        self.log("🚀 Starting Git push release pipeline...")
        
        # Start Git push in a non-blocking background thread
        threading.Thread(target=self.run_push_thread, daemon=True).start()

    def run_push_thread(self):
        try:
            exe_path = os.path.join(current_dir, "dist", "XenoScript.exe")
            if not os.path.exists(exe_path):
                # Fallback to lower case if named xenoscript.exe
                exe_path = os.path.join(current_dir, "dist", "xenoscript.exe")
                if not os.path.exists(exe_path):
                    self.root.after(0, lambda: messagebox.showerror("Error", "Compiled executable not found inside 'dist/' folder.\nPlease run 'Build Executable' first."))
                    return
            
            # Save token just in case
            token = self.token_entry.get().strip()
            self.save_github_token(token)
            
            # 1. Update local C:\XenoScript installation if it exists
            local_install_dir = r"C:\XenoScript"
            if os.path.exists(local_install_dir):
                self.root.after(0, lambda: self.log("📤 Updating local installation at C:\\XenoScript..."))
                try:
                    shutil.copy2(exe_path, os.path.join(local_install_dir, "XenoScript.exe"))
                    shutil.copy2(exe_path, os.path.join(local_install_dir, "xenoscript.exe"))
                    shutil.copy2(version_file, os.path.join(local_install_dir, "version.json"))
                except Exception as ex:
                    self.root.after(0, lambda: self.log(f"   (Local C:\\XenoScript update skipped: {str(ex)})"))

            # 2. Stage only version.json and the setup file (ignore other source file edits)
            self.root.after(0, lambda: self.log("📂 Staging only version.json and the setup installer..."))
            
            # Find the active setup file
            setup_file = None
            for fname in ["XenoScript_Setup.exe", "setup_xenoscript.exe", "XenoScriptSetup.exe"]:
                path = os.path.join(current_dir, "dist", fname)
                if os.path.exists(path):
                    setup_file = path
                    break
            
            if not setup_file:
                self.root.after(0, lambda: self.log("❌ Error: Setup installer file not found inside 'dist/' folder!"))
                self.root.after(0, lambda: messagebox.showerror("Push Failed", "Setup installer file not found."))
                return

            rel_setup_path = os.path.relpath(setup_file, current_dir)
            
            # Stage version.json
            ret, out = self.run_git_cmd(["git", "add", "version.json"])
            if ret != 0:
                self.root.after(0, lambda: self.log("❌ Error: git add version.json failed!"))
                self.root.after(0, lambda: messagebox.showerror("Push Failed", "git add version.json failed."))
                return
            
            # 3. Commit changes
            new_ver = self.ver_entry.get().strip()
            changes = [line.strip() for line in self.change_text.get("1.0", tk.END).split("\n") if line.strip()]
            commit_msg = f"Release v{new_ver}\n\nChangelog:\n" + "\n".join([f"- {c}" for c in changes])
            
            self.root.after(0, lambda: self.log("💾 Committing changes with git commit..."))
            ret, out = self.run_git_cmd(["git", "commit", "-m", commit_msg])
            
            # If nothing to commit, that's fine, we can continue to push.
            if ret != 0 and "nothing to commit" not in out.lower() and "working tree clean" not in out.lower():
                self.root.after(0, lambda: self.log("❌ Error: git commit failed!"))
                self.root.after(0, lambda: messagebox.showerror("Push Failed", "git commit command failed."))
                return
            
            # 4. Push to remote
            branch = self.git_branch if self.git_branch != "Unknown Branch" else "main"
            self.root.after(0, lambda: self.log(f"📤 Pushing to GitHub (origin/{branch})..."))
            ret, out = self.run_git_cmd(["git", "push", "origin", branch])
            if ret != 0:
                self.root.after(0, lambda: self.log("❌ Error: git push failed!"))
                self.root.after(0, lambda: messagebox.showerror("Push Failed", "git push command failed."))
                return

            # 5. Create Tag and Push Tag to origin
            self.root.after(0, lambda: self.log(f"🏷️ Creating tag v{new_ver} locally..."))
            ret, out = self.run_git_cmd(["git", "tag", "-a", f"v{new_ver}", "-m", f"Release v{new_ver}"])
            
            self.root.after(0, lambda: self.log(f"📤 Pushing tag v{new_ver} to origin..."))
            self.run_git_cmd(["git", "push", "origin", f"v{new_ver}"])
            
            # 6. GitHub Release via REST API
            if token:
                owner, repo = self.parse_github_url(self.git_repo)
                if owner and repo:
                    headers = {
                        "Accept": "application/vnd.github+json",
                        "Authorization": f"Bearer {token}",
                        "X-GitHub-Api-Version": "2022-11-28"
                    }
                    
                    self.root.after(0, lambda: self.log(f"🔍 Checking if GitHub Release for v{new_ver} already exists..."))
                    get_url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/v{new_ver}"
                    resp = requests.get(get_url, headers=headers)
                    release_info = None
                    
                    if resp.status_code == 200:
                        release_info = resp.json()
                        self.root.after(0, lambda: self.log(f"ℹ️ Existing Release for v{new_ver} found. Re-using it."))
                    elif resp.status_code == 404:
                        # Create new release
                        self.root.after(0, lambda: self.log(f"🌐 Creating new GitHub Release v{new_ver}..."))
                        release_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
                        release_data = {
                            "tag_name": f"v{new_ver}",
                            "target_commitish": branch,
                            "name": f"v{new_ver}",
                            "body": "\n".join([f"- {c}" for c in changes]) if changes else f"Release v{new_ver}",
                            "draft": False,
                            "prerelease": False
                        }
                        create_resp = requests.post(release_url, headers=headers, json=release_data)
                        if create_resp.status_code in (200, 201):
                            release_info = create_resp.json()
                            self.root.after(0, lambda: self.log(f"✅ GitHub Release v{new_ver} created successfully!"))
                        else:
                            self.root.after(0, lambda: self.log(f"❌ Failed to create GitHub Release: {create_resp.status_code} - {create_resp.text}"))
                    else:
                        self.root.after(0, lambda: self.log(f"❌ Failed to query GitHub Release: {resp.status_code} - {resp.text}"))
                    
                    if release_info:
                        asset_name = os.path.basename(setup_file)
                        
                        # Check if the asset already exists on this release
                        existing_asset = None
                        for asset in release_info.get("assets", []):
                            if asset["name"] == asset_name:
                                existing_asset = asset
                                break
                        
                        if existing_asset:
                            asset_id = existing_asset["id"]
                            self.root.after(0, lambda: self.log(f"🗑️ Found existing asset {asset_name} (ID: {asset_id}) on release. Deleting it first..."))
                            delete_url = f"https://api.github.com/repos/{owner}/{repo}/releases/assets/{asset_id}"
                            del_resp = requests.delete(delete_url, headers=headers)
                            if del_resp.status_code in (200, 204):
                                self.root.after(0, lambda: self.log(f"✅ Deleted old asset {asset_name}."))
                            else:
                                self.root.after(0, lambda: self.log(f"⚠️ Failed to delete old asset: {del_resp.status_code} - {del_resp.text}"))
                        
                        self.root.after(0, lambda: self.log(f"📤 Uploading {asset_name} to GitHub Release (this may take a moment)..."))
                        upload_url_template = release_info.get("upload_url", "")
                        if upload_url_template:
                            upload_url = upload_url_template.split("{")[0]
                            upload_url = f"{upload_url}?name={asset_name}"
                            
                            upload_headers = {
                                "Accept": "application/vnd.github+json",
                                "Authorization": f"Bearer {token}",
                                "Content-Type": "application/octet-stream",
                                "X-GitHub-Api-Version": "2022-11-28"
                            }
                            
                            with open(setup_file, "rb") as f:
                                file_data = f.read()
                                
                            upload_resp = requests.post(upload_url, headers=upload_headers, data=file_data, timeout=300)
                            if upload_resp.status_code in (200, 201):
                                self.root.after(0, lambda: self.log(f"🎉 Asset {asset_name} uploaded successfully to GitHub Release!"))
                            else:
                                self.root.after(0, lambda: self.log(f"❌ Failed to upload asset to Release: {upload_resp.status_code} - {upload_resp.text}"))
                        else:
                            self.root.after(0, lambda: self.log("❌ Could not get upload_url from release response."))
                else:
                    self.root.after(0, lambda: self.log(f"⚠️ Could not parse owner/repo from Git URL: {self.git_repo}"))
            else:
                self.root.after(0, lambda: self.log("⚠️ GitHub Token (PAT) not provided. Skipping GitHub Release & asset upload."))
                
            self.root.after(0, lambda: self.log("✅ DEPLOYMENT PIPELINE COMPLETE!\nAll assets pushed successfully to GitHub."))
            self.root.after(0, lambda: messagebox.showinfo("Push Success", f"XenoScript executable and version details successfully pushed to GitHub on branch '{branch}'!"))
            
        except Exception as e:
            err_msg = str(e)
            self.root.after(0, lambda m=err_msg: self.log(f"❌ Push Exception: {m}"))
            self.root.after(0, lambda m=err_msg: messagebox.showerror("Push Failed", f"An error occurred during push: {m}"))
        finally:
            self.root.after(0, self._enable_buttons)

    # --- REGISTRATION KEY MANAGEMENT & VERIFICATION ---
    def generate_custom_key(self):
        # Generate random letters and digits for the first two segments
        L = [random.choice(string.ascii_uppercase) for _ in range(4)]
        D = [random.randint(0, 9) for _ in range(4)]
        
        # Calculate checksum characters for the third segment
        val_L = [ord(char) - ord('A') for char in L]
        
        # L4 = (val_L[0] * 3 + val_L[1] * 7 + val_L[2] * 11 + val_L[3] * 13) % 26
        val_L4 = (val_L[0] * 3 + val_L[1] * 7 + val_L[2] * 11 + val_L[3] * 13) % 26
        L4 = chr(val_L4 + ord('A'))
        
        # D4 = (D[0] * 3 + D[1] * 7 + D[2] * 2 + D[3] * 5) % 10
        D4 = (D[0] * 3 + D[1] * 7 + D[2] * 2 + D[3] * 5) % 10
        
        # L5 = (val_L[0] * 17 + val_L[1] * 19 + val_L[2] * 23 + val_L[3] * 29) % 26
        val_L5 = (val_L[0] * 17 + val_L[1] * 19 + val_L[2] * 23 + val_L[3] * 29) % 26
        L5 = chr(val_L5 + ord('A'))
        
        # D5 = (D[0] * 7 + D[1] * 9 + D[2] * 3 + D[3] * 1) % 10
        D5 = (D[0] * 7 + D[1] * 9 + D[2] * 3 + D[3] * 1) % 10
        
        # Construct key segments
        seg1 = f"{L[0]}{D[0]}{L[1]}{D[1]}"
        seg2 = f"{L[2]}{D[2]}{L[3]}{D[3]}"
        seg3 = f"{L4}{D4}{L5}{D5}"
        
        return f"{seg1}-{seg2}-{seg3}"

    def refresh_keys(self):
        self.btn_refresh_keys.configure(state=tk.DISABLED)
        self.log("🗄️ Fetching registration keys from Cloudflare D1...")
        threading.Thread(target=self.run_fetch_keys_thread, daemon=True).start()

    def run_fetch_keys_thread(self):
        try:
            creationflags = 0
            npx_cmd = "npx.cmd" if os.name == 'nt' else "npx"
            if os.name == 'nt':
                creationflags = 0x08000000
                
            cmd = [npx_cmd, "wrangler", "d1", "execute", "xenohead_data", "--command", "SELECT * FROM XenoScript ORDER BY AutoKey DESC;", "--remote", "--json"]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=creationflags,
                cwd=current_dir
            )
            out, err = process.communicate()
            
            if process.returncode == 0:
                try:
                    data = json.loads(out)
                    rows = data[0].get("results", [])
                    self.root.after(0, lambda r=rows: self.populate_keys_tree(r))
                    self.root.after(0, lambda count=len(rows): self.log(f"✅ Fetched {count} registration keys successfully."))
                except Exception as ex:
                    ex_msg = str(ex)
                    self.root.after(0, lambda msg=ex_msg: self.log(f"❌ Error parsing D1 JSON response: {msg}"))
            else:
                err_msg = err.strip()
                self.root.after(0, lambda msg=err_msg: self.log(f"❌ Failed to query D1 database: {msg}"))
        except Exception as e:
            err_msg = str(e)
            self.root.after(0, lambda msg=err_msg: self.log(f"❌ Exception querying D1: {msg}"))
        finally:
            self.root.after(0, lambda: self.btn_refresh_keys.configure(state=tk.NORMAL))

    def populate_keys_tree(self, rows):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for row in rows:
            autokey = row.get("AutoKey", "")
            appname = row.get("AppName", "")
            authkey = row.get("Authkey", "")
            regkey = row.get("Regkey", "")
            datereg = row.get("DateRegistered", "")
            regname = row.get("RegName", "")
            regemail = row.get("RegEmail", "")
            active = row.get("Active", "")
            
            self.tree.insert("", tk.END, values=(autokey, appname, authkey, regkey, regname, regemail, datereg, active))

    def open_add_key_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Generate & Add Registration Key")
        dialog.geometry("450x450")
        dialog.configure(bg=self.colors["bg_dark"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        lbl_header = tk.Label(dialog, text="Generate New Key", font=("Segoe UI", 12, "bold"), bg=self.colors["bg_dark"], fg=self.colors["accent_blue"])
        lbl_header.pack(pady=15)
        
        # Pre-generate the registration key so it can be displayed
        reg_key = self.generate_custom_key()
        
        key_frame = tk.Frame(dialog, bg=self.colors["card_bg"], bd=1, relief=tk.SOLID, padx=10, pady=10)
        key_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        lbl_key_title = tk.Label(key_frame, text="Generated Key (Verifiable):", font=("Segoe UI", 9, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_muted"])
        lbl_key_title.pack(anchor=tk.W)
        
        lbl_key_val = tk.Label(key_frame, text=reg_key, font=("Consolas", 14, "bold"), bg=self.colors["card_bg"], fg=self.colors["accent_amber"])
        lbl_key_val.pack(pady=5)
        
        form_frame = tk.Frame(dialog, bg=self.colors["bg_dark"])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        
        fields = [
            ("App Name:", "AppName", "XenoScript"),
            ("Reg Name:", "RegName", ""),
            ("Reg Email:", "RegEmail", ""),
            ("Active (y/n):", "Active", "y")
        ]
        
        entries = {}
        for i, (label_text, field_name, default_val) in enumerate(fields):
            lbl = tk.Label(form_frame, text=label_text, font=("Segoe UI", 9, "bold"), bg=self.colors["bg_dark"], fg=self.colors["text_light"])
            lbl.grid(row=i, column=0, sticky=tk.W, pady=8)
            
            entry = tk.Entry(form_frame, font=("Segoe UI", 9), bg=self.colors["card_bg"], fg=self.colors["text_light"], insertbackground="white", bd=1, relief=tk.SOLID, width=30)
            entry.grid(row=i, column=1, sticky=tk.W, padx=10, pady=8)
            entry.insert(0, default_val)
            entries[field_name] = entry
            
        lbl_status = tk.Label(dialog, text="", font=("Segoe UI", 8), bg=self.colors["bg_dark"], fg=self.colors["accent_amber"])
        lbl_status.pack(pady=5)
        
        def on_save():
            app_name = entries["AppName"].get().strip()
            reg_name = entries["RegName"].get().strip()
            reg_email = entries["RegEmail"].get().strip()
            active = entries["Active"].get().strip().lower()
            
            if not app_name:
                lbl_status.configure(text="App Name is required!")
                return
            if not reg_name:
                lbl_status.configure(text="Reg Name is required!")
                return
            if not reg_email:
                lbl_status.configure(text="Reg Email is required!")
                return
            if active not in ('y', 'n'):
                lbl_status.configure(text="Active must be 'y' or 'n'!")
                return
                
            date_registered = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            lbl_status.configure(text="Saving to D1 remote database...")
            btn_save.configure(state=tk.DISABLED)
            
            def run_save():
                success = self.save_key_to_d1(app_name, "", reg_key, reg_name, reg_email, active, date_registered)
                if success:
                    def success_callback():
                        dialog.destroy()
                        self.refresh_keys()
                    self.root.after(0, success_callback)
                else:
                    self.root.after(0, lambda: lbl_status.configure(text="Failed to save to D1 database."))
                    self.root.after(0, lambda: btn_save.configure(state=tk.NORMAL))

            threading.Thread(target=run_save, daemon=True).start()
                
        btn_save = tk.Button(
            dialog, 
            text="Generate & Save Key", 
            font=("Segoe UI", 10, "bold"), 
            bg=self.colors["accent_green"], 
            fg=self.colors["text_light"],
            activebackground="#0e9f6e",
            activeforeground="white",
            bd=0, 
            pady=8,
            padx=15,
            cursor="hand2",
            command=on_save
        )
        btn_save.pack(pady=20)

    def save_key_to_d1(self, app_name, auth_key, reg_key, reg_name, reg_email, active, date_registered):
        try:
            creationflags = 0
            npx_cmd = "npx.cmd" if os.name == 'nt' else "npx"
            if os.name == 'nt':
                creationflags = 0x08000000
                
            esc_app_name = app_name.replace("'", "''")
            esc_auth_key = auth_key.replace("'", "''")
            esc_reg_key = reg_key.replace("'", "''")
            esc_reg_name = reg_name.replace("'", "''")
            esc_reg_email = reg_email.replace("'", "''")
            esc_active = active.replace("'", "''")
            esc_date = date_registered.replace("'", "''")
            
            sql = f"INSERT INTO XenoScript (AppName, Authkey, Regkey, DateRegistered, RegName, RegEmail, Active) VALUES ('{esc_app_name}', '{esc_auth_key}', '{esc_reg_key}', '{esc_date}', '{esc_reg_name}', '{esc_reg_email}', '{esc_active}');"
            
            cmd = [npx_cmd, "wrangler", "d1", "execute", "xenohead_data", "--command", sql, "--remote"]
            
            self.log(f"🗄️ Adding key to D1: {reg_key} ({reg_name})")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=creationflags,
                cwd=current_dir
            )
            out, err = process.communicate()
            
            if process.returncode == 0:
                self.log(f"🎉 Successfully saved key '{reg_key}' to Cloudflare D1.")
                return True
            else:
                self.log(f"❌ D1 Write Error: {err.strip()}")
                return False
        except Exception as e:
            self.log(f"❌ Exception writing to D1: {str(e)}")
            return False

    def show_reg_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.reg_menu.post(event.x_root, event.y_root)

    def open_edit_key_dialog(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a registration key from the list to edit.")
            return
            
        item_values = self.tree.item(selected[0], "values")
        if not item_values or len(item_values) < 8:
            return
            
        autokey, app_name, auth_key, reg_key, reg_name, reg_email, date_reg, active = item_values
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Registration Key")
        dialog.geometry("450x480")
        dialog.configure(bg=self.colors["bg_dark"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        lbl_header = tk.Label(dialog, text="Edit Registration Key Details", font=("Segoe UI", 12, "bold"), bg=self.colors["bg_dark"], fg=self.colors["accent_blue"])
        lbl_header.pack(pady=15)
        
        key_frame = tk.Frame(dialog, bg=self.colors["card_bg"], bd=1, relief=tk.SOLID, padx=10, pady=10)
        key_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        lbl_key_title = tk.Label(key_frame, text="Registration Key (Read-Only):", font=("Segoe UI", 9, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_muted"])
        lbl_key_title.pack(anchor=tk.W)
        
        lbl_key_val = tk.Label(key_frame, text=reg_key, font=("Consolas", 12, "bold"), bg=self.colors["card_bg"], fg=self.colors["accent_amber"])
        lbl_key_val.pack(pady=5)
        
        form_frame = tk.Frame(dialog, bg=self.colors["bg_dark"])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        
        fields = [
            ("App Name:", "AppName", app_name),
            ("Auth Key (Hardware ID):", "Authkey", auth_key),
            ("Reg Name:", "RegName", reg_name),
            ("Reg Email:", "RegEmail", reg_email),
            ("Active (y/n):", "Active", active)
        ]
        
        entries = {}
        for i, (label_text, field_name, val) in enumerate(fields):
            lbl = tk.Label(form_frame, text=label_text, font=("Segoe UI", 9, "bold"), bg=self.colors["bg_dark"], fg=self.colors["text_light"])
            lbl.grid(row=i, column=0, sticky=tk.W, pady=8)
            
            entry = tk.Entry(form_frame, font=("Segoe UI", 9), bg=self.colors["card_bg"], fg=self.colors["text_light"], insertbackground="white", bd=1, relief=tk.SOLID, width=30)
            entry.grid(row=i, column=1, sticky=tk.W, padx=10, pady=8)
            entry.insert(0, val)
            entries[field_name] = entry
            
        lbl_status = tk.Label(dialog, text="", font=("Segoe UI", 8), bg=self.colors["bg_dark"], fg=self.colors["accent_amber"])
        lbl_status.pack(pady=5)
        
        def on_save():
            new_app_name = entries["AppName"].get().strip()
            new_auth_key = entries["Authkey"].get().strip()
            new_reg_name = entries["RegName"].get().strip()
            new_reg_email = entries["RegEmail"].get().strip()
            new_active = entries["Active"].get().strip().lower()
            
            if not new_app_name:
                lbl_status.configure(text="App Name is required!")
                return
            if not new_reg_name:
                lbl_status.configure(text="Reg Name is required!")
                return
            if not new_reg_email:
                lbl_status.configure(text="Reg Email is required!")
                return
            if new_active not in ('y', 'n'):
                lbl_status.configure(text="Active must be 'y' or 'n'!")
                return
                
            lbl_status.configure(text="Updating D1 remote database...")
            btn_save.configure(state=tk.DISABLED)
            
            def run_update():
                success = self.update_key_in_d1(autokey, new_app_name, new_auth_key, new_reg_name, new_reg_email, new_active)
                if success:
                    def success_callback():
                        dialog.destroy()
                        self.refresh_keys()
                    self.root.after(0, success_callback)
                else:
                    self.root.after(0, lambda: lbl_status.configure(text="Failed to update key in D1 database."))
                    self.root.after(0, lambda: btn_save.configure(state=tk.NORMAL))

            threading.Thread(target=run_update, daemon=True).start()
                
        btn_save = tk.Button(
            dialog, 
            text="Save Changes", 
            font=("Segoe UI", 10, "bold"), 
            bg=self.colors["accent_green"], 
            fg=self.colors["text_light"],
            activebackground="#0e9f6e",
            activeforeground="white",
            bd=0, 
            pady=8,
            padx=15,
            cursor="hand2",
            command=on_save
        )
        btn_save.pack(pady=15)

    def update_key_in_d1(self, autokey, app_name, auth_key, reg_name, reg_email, active):
        try:
            creationflags = 0
            npx_cmd = "npx.cmd" if os.name == 'nt' else "npx"
            if os.name == 'nt':
                creationflags = 0x08000000
                
            esc_app_name = app_name.replace("'", "''")
            esc_auth_key = auth_key.replace("'", "''")
            esc_reg_name = reg_name.replace("'", "''")
            esc_reg_email = reg_email.replace("'", "''")
            esc_active = active.replace("'", "''")
            
            sql = f"UPDATE XenoScript SET AppName = '{esc_app_name}', Authkey = '{esc_auth_key}', RegName = '{esc_reg_name}', RegEmail = '{esc_reg_email}', Active = '{esc_active}' WHERE AutoKey = {int(autokey)};"
            
            cmd = [npx_cmd, "wrangler", "d1", "execute", "xenohead_data", "--command", sql, "--remote"]
            
            self.log(f"🗄️ Updating key ID {autokey} in D1...")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=creationflags,
                cwd=current_dir
            )
            out, err = process.communicate()
            
            if process.returncode == 0:
                self.log(f"🎉 Successfully updated key ID {autokey} in Cloudflare D1.")
                return True
            else:
                self.log(f"❌ D1 Update Error: {err.strip()}")
                return False
        except Exception as e:
            self.log(f"❌ Exception updating D1: {str(e)}")
            return False

    def copy_selected_key(self):
        selected = self.tree.selection()
        if selected:
            item_values = self.tree.item(selected[0], "values")
            if len(item_values) > 3:
                key = item_values[3]
                self.root.clipboard_clear()
                self.root.clipboard_append(key)
                self.log(f"📋 Copied key to clipboard: {key}")

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
