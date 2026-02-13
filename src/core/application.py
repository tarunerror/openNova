"""
Main application orchestrator with multi-process architecture.
"""
import sys
import multiprocessing as mp
from multiprocessing import Process, Queue
import signal
import time


def run_gui_frontend(cmd_queue: Queue, resp_queue: Queue):
    """Process entrypoint for GUI frontend."""
    try:
        from src.gui.main_window import run_gui
        run_gui(cmd_queue, resp_queue)
    except Exception as e:
        print(f"[✗] GUI Process Error: {e}")
        import traceback
        traceback.print_exc()


def run_ai_backend(cmd_queue: Queue, resp_queue: Queue):
    """Process entrypoint for AI backend."""
    try:
        from src.core.ai_backend import AIBackend
        backend = AIBackend(cmd_queue, resp_queue)
        backend.run()
    except Exception as e:
        print(f"[✗] AI Backend Error: {e}")
        import traceback
        traceback.print_exc()


class Application:
    """Main application coordinator."""
    
    def __init__(self):
        """Initialize the application."""
        self.gui_process = None
        self.ai_process = None
        self.command_queue = Queue()  # GUI -> AI
        self.response_queue = Queue()  # AI -> GUI
        
    def run(self):
        """Start the application with multi-process architecture."""
        print("\n[*] Launching Multi-Process Architecture...")
        
        # Handle graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Start AI Backend Process
            print("[*] Starting AI Backend Process...")
            self.ai_process = Process(
                target=run_ai_backend,
                args=(self.command_queue, self.response_queue),
                name="AI_Backend"
            )
            self.ai_process.start()
            
            # Start GUI Frontend Process
            print("[*] Starting GUI Frontend Process...")
            self.gui_process = Process(
                target=run_gui_frontend,
                args=(self.command_queue, self.response_queue),
                name="GUI_Frontend"
            )
            self.gui_process.start()
            
            print("[✓] All processes started successfully.")
            print("[*] Press Ctrl+C to shutdown.\n")
            
            # Wait for processes
            self.gui_process.join()
            
        except KeyboardInterrupt:
            print("\n[*] Shutdown signal received...")
        except Exception as e:
            print(f"\n[✗] Error: {e}")
        finally:
            self._cleanup()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print("\n[*] Shutdown signal received...")
        self._cleanup()
        sys.exit(0)
    
    def _cleanup(self):
        """Clean up processes."""
        print("[*] Cleaning up processes...")
        
        if self.ai_process and self.ai_process.is_alive():
            print("[*] Terminating AI Backend...")
            self.ai_process.terminate()
            self.ai_process.join(timeout=2)
        
        if self.gui_process and self.gui_process.is_alive():
            print("[*] Terminating GUI Frontend...")
            self.gui_process.terminate()
            self.gui_process.join(timeout=2)
        
        print("[✓] Cleanup complete.")


if __name__ == "__main__":
    # For Windows multiprocessing support
    mp.freeze_support()
