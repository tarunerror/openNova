"""
AI Backend Process - The "Brain" of the agent.
Handles LLM inference, planning, and coordination.
"""
from multiprocessing import Queue
import time
import logging
from pathlib import Path


# Setup logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "ai_backend.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AIBackend")


class AIBackend:
    """AI Backend coordinator."""
    
    def __init__(self, command_queue: Queue, response_queue: Queue):
        """Initialize the AI backend."""
        self.command_queue = command_queue
        self.response_queue = response_queue
        self.running = False
        
        logger.info("AI Backend initialized")
    
    def run(self):
        """Main loop for the AI backend."""
        self.running = True
        logger.info("AI Backend started - waiting for commands...")
        
        try:
            while self.running:
                # Check for commands from GUI
                if not self.command_queue.empty():
                    command = self.command_queue.get()
                    logger.info(f"Received command: {command}")
                    
                    # Process command
                    response = self._process_command(command)
                    
                    # Send response back to GUI
                    self.response_queue.put(response)
                
                time.sleep(0.1)  # Prevent CPU spinning
                
        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
        except Exception as e:
            logger.error(f"Error in AI Backend: {e}", exc_info=True)
        finally:
            self.running = False
            logger.info("AI Backend stopped")
    
    def _process_command(self, command: dict) -> dict:
        """Process incoming commands."""
        cmd_type = command.get("type", "unknown")
        
        if cmd_type == "test":
            return {
                "type": "response",
                "status": "success",
                "message": "AI Backend is operational!"
            }
        
        elif cmd_type == "transcribe":
            # Handle transcription (will be implemented later)
            text = command.get("text", "")
            return {
                "type": "response",
                "status": "success",
                "message": f"Processing: {text}"
            }
        
        else:
            return {
                "type": "response",
                "status": "error",
                "message": f"Unknown command type: {cmd_type}"
            }
