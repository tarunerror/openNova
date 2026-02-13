"""
Test runner - runs without admin elevation
Use this for quick testing. Some features may be limited.
"""
import sys

def main():
    print("=" * 60)
    print("AI Agent - Test Mode (No Admin Required)")
    print("=" * 60)
    print("[!] Running in test mode - admin features disabled")
    print()
    
    # Import and start the main application
    from src.core.application import Application
    
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
