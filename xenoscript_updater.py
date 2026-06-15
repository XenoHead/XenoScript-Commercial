import sys
import os
import time
import subprocess
import ctypes
import urllib.request
import tempfile
import threading
import tkinter as tk
from tkinter import ttk

def hard_kill(pid):
    try:
        os.system(f"taskkill /F /PID {pid} >nul 2>&1")
    except:
        pass
    try:
        os.system("taskkill /F /IM xenoscript.exe >nul 2>&1")
    except:
        pass
    time.sleep(1.5)

def download_and_run(url, asset_name, token, root, progress_var, status_var):
    temp_dir = tempfile.gettempdir()
    dest_path = os.path.join(temp_dir, asset_name)
    
    headers = {"Accept": "application/octet-stream"}
    if token:
        headers["Authorization"] = f"token {token}"
        
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=45) as response:
            total_size = int(response.info().get('Content-Length', -1))
            downloaded = 0
            block_size = 8192
            
            with open(dest_path, 'wb') as f:
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    f.write(buffer)
                    downloaded += len(buffer)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        progress_var.set(progress)
                        status_var.set(f"Downloading... {int(progress)}%")
                        
        status_var.set("Starting installer...")
        time.sleep(0.5)
        
        subprocess.Popen([dest_path], shell=False)
        root.quit()
        
    except Exception as e:
        status_var.set(f"Error: {str(e)}")
        time.sleep(3)
        root.quit()

def main():
    installer_path = None
    url = None
    asset_name = "XenoScript_Setup.exe"
    pid_to_wait = None
    token = None
    
    args = sys.argv[1:]
    for i in range(len(args)):
        if args[i] == "--installer" and i + 1 < len(args):
            installer_path = args[i+1]
        elif args[i] == "--url" and i + 1 < len(args):
            url = args[i+1]
        elif args[i] == "--name" and i + 1 < len(args):
            asset_name = args[i+1]
        elif args[i] == "--pid" and i + 1 < len(args):
            try:
                pid_to_wait = int(args[i+1])
            except ValueError:
                pass
        elif args[i] == "--token" and i + 1 < len(args):
            token = args[i+1]
            
    if pid_to_wait:
        hard_kill(pid_to_wait)
    else:
        # Just in case, try to kill xenoscript anyway if no PID was provided
        try:
            os.system("taskkill /F /IM xenoscript.exe >nul 2>&1")
        except:
            pass
        time.sleep(1.0)
        
    if url:
        root = tk.Tk()
        root.title("XenoScript Updater")
        root.geometry("400x120")
        root.eval('tk::PlaceWindow . center')
        root.resizable(False, False)
        
        style = ttk.Style()
        style.theme_use('clam')
        
        status_var = tk.StringVar()
        status_var.set("Connecting...")
        
        lbl = ttk.Label(root, textvariable=status_var, font=("Segoe UI", 10))
        lbl.pack(pady=(15, 5))
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100, length=350)
        progress_bar.pack(pady=(5, 15))
        
        threading.Thread(target=download_and_run, args=(url, asset_name, token, root, progress_var, status_var), daemon=True).start()
        
        root.mainloop()
    elif installer_path and os.path.exists(installer_path):
        try:
            subprocess.Popen([installer_path], shell=False)
        except Exception:
            pass
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
