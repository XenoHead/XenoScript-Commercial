import sys
import os
import time
import subprocess
import ctypes

def main():
    # Parse arguments: --installer <path> --pid <pid>
    installer_path = None
    pid_to_wait = None
    
    args = sys.argv[1:]
    for i in range(len(args)):
        if args[i] == "--installer" and i + 1 < len(args):
            installer_path = args[i+1]
        elif args[i] == "--pid" and i + 1 < len(args):
            try:
                pid_to_wait = int(args[i+1])
            except ValueError:
                pass

    if not installer_path:
        sys.exit(1)

    # 1. Wait for parent process to exit if PID is provided
    if pid_to_wait:
        # SYNCHRONIZE access right is required for WaitForSingleObject
        SYNCHRONIZE = 0x00100000
        process_handle = ctypes.windll.kernel32.OpenProcess(SYNCHRONIZE, False, pid_to_wait)
        if process_handle:
            # Wait up to 10 seconds for the process to exit
            ctypes.windll.kernel32.WaitForSingleObject(process_handle, 10000)
            ctypes.windll.kernel32.CloseHandle(process_handle)
            
    # Add a short delay to ensure any remaining OS locks are fully released
    time.sleep(1.5)

    # 2. Launch the installer
    if os.path.exists(installer_path):
        try:
            # Spawn the installer process detached and exit
            subprocess.Popen([installer_path], shell=False)
        except Exception:
            sys.exit(1)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
