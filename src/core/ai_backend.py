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
        
        # Initialize audio components
        self._init_audio()
        
        # Initialize brain components
        self._init_brain()
        
        logger.info("AI Backend initialized")
    
    def _init_audio(self):
        """Initialize audio components."""
        try:
            from src.audio.recorder import AudioRecorder
            from src.audio.stt import SpeechToText
            from src.audio.tts import TextToSpeech
            
            self.recorder = AudioRecorder()
            self.stt = SpeechToText(model_size="base")
            self.tts = TextToSpeech()
            
            logger.info("Audio components initialized")
        except Exception as e:
            logger.error(f"Error initializing audio: {e}")
            self.recorder = None
            self.stt = None
            self.tts = None
    
    def _init_brain(self):
        """Initialize LLM and planning components."""
        try:
            from src.llm.planner import planner
            from src.memory.manager import memory
            from src.actions.executor import action_executor
            
            self.planner = planner
            self.memory = memory
            self.executor = action_executor
            
            logger.info("Brain components initialized")
        except Exception as e:
            logger.error(f"Error initializing brain: {e}")
            self.planner = None
            self.memory = None
            self.executor = None
    
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
        
        elif cmd_type == "start_recording":
            # Start audio recording
            if self.recorder:
                success = self.recorder.start_recording()
                if success:
                    return {
                        "type": "response",
                        "status": "success",
                        "message": "Recording started"
                    }
                else:
                    return {
                        "type": "response",
                        "status": "error",
                        "message": "Failed to start recording"
                    }
            else:
                return {
                    "type": "response",
                    "status": "error",
                    "message": "Audio recorder not available"
                }
        
        elif cmd_type == "stop_recording":
            # Stop recording and transcribe
            if self.recorder and self.stt:
                audio_data = self.recorder.stop_recording()
                
                if len(audio_data) > 0:
                    # Transcribe
                    text = self.stt.transcribe_numpy(audio_data)
                    
                    if text:
                        logger.info(f"Transcribed: {text}")
                        
                        # Store in memory
                        if self.memory:
                            self.memory.remember(
                                content=f"User said: {text}",
                                metadata={"type": "command"}
                            )
                        
                        # Create action plan
                        if self.planner:
                            plan = self.planner.create_plan(text)
                            
                            if plan:
                                # Check if confirmation needed
                                needs_confirm = self.planner.needs_confirmation(plan)
                                
                                plan_summary = f"Created plan with {len(plan)} steps"
                                logger.info(plan_summary)
                                
                                # Speak back understanding
                                if self.tts:
                                    if needs_confirm:
                                        self.tts.speak(f"I will {text}. Please confirm to proceed.")
                                    else:
                                        self.tts.speak(f"Understood: {text}. Executing now.")
                                
                                return {
                                    "type": "response",
                                    "status": "success",
                                    "message": f"Command: {text}",
                                    "plan": plan,
                                    "needs_confirmation": needs_confirm
                                }
                            else:
                                if self.tts:
                                    self.tts.speak("I'm not sure how to do that.")
                                
                                return {
                                    "type": "response",
                                    "status": "error",
                                    "message": "Could not create action plan"
                                }
                        else:
                            # Just echo back if no planner
                            if self.tts:
                                self.tts.speak(f"I heard: {text}")
                            
                            return {
                                "type": "response",
                                "status": "success",
                                "message": f"Transcribed: {text}"
                            }
                    else:
                        return {
                            "type": "response",
                            "status": "error",
                            "message": "Could not transcribe audio"
                        }
                else:
                    return {
                        "type": "response",
                        "status": "error",
                        "message": "No audio recorded"
                    }
            else:
                return {
                    "type": "response",
                    "status": "error",
                    "message": "Audio systems not available"
                }
        
        elif cmd_type == "transcribe":
            # Handle transcription (will be implemented later)
            text = command.get("text", "")
            return {
                "type": "response",
                "status": "success",
                "message": f"Processing: {text}"
            }
        
        elif cmd_type == "execute_plan":
            # Execute an action plan
            plan = command.get("plan", [])
            
            if self.executor and plan:
                result = self.executor.execute_plan(plan)
                
                success = result.get("success", False)
                message = f"Executed {result.get('successful_steps', 0)}/{result.get('total_steps', 0)} steps"
                
                # Speak result
                if self.tts:
                    if success:
                        self.tts.speak("Task completed successfully.")
                    else:
                        self.tts.speak("Task completed with some errors.")
                
                return {
                    "type": "response",
                    "status": "success" if success else "partial",
                    "message": message,
                    "result": result
                }
            else:
                return {
                    "type": "response",
                    "status": "error",
                    "message": "No plan to execute or executor not available"
                }
        
        else:
            return {
                "type": "response",
                "status": "error",
                "message": f"Unknown command type: {cmd_type}"
            }
