"""
Enterprise Desktop AI Agent
Main entry point with Admin elevation support
"""
import ctypes
import sys
import os


def is_admin():
    """Check if the script is running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin():
    """Re-launch the script with admin privileges."""
    if sys.platform != 'win32':
        print("Admin elevation is only supported on Windows.")
        return False
    
    script = os.path.abspath(sys.argv[0])
    params = ' '.join([script] + sys.argv[1:])
    
    try:
        # ShellExecuteW returns a value > 32 on success
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, None, 1
        )
        return ret > 32
    except Exception as e:
        print(f"Failed to elevate privileges: {e}")
        return False


def main():
    """Main application entry point."""
    print("=" * 60)
    print("Enterprise Desktop AI Agent - Starting...")
    print("=" * 60)
    
    # Check for admin privileges
    if not is_admin():
        print("\n[!] This application requires Administrator privileges.")
        print("[*] Attempting to restart with elevated privileges...")
        
        if run_as_admin():
            print("[✓] Elevated process started. Exiting current instance.")
            sys.exit(0)
        else:
            print("[✗] Failed to obtain admin privileges.")
            print("[!] Continuing without admin - some features may not work.")
            # Removed input() so it doesn't pause
    else:
        print("[✓] Running with Administrator privileges.")
    
    # Import and start the main application
    from src.core.application import Application
    
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
