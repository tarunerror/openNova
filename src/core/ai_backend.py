"""
AI Backend Process - The "Brain" of the agent.
Handles LLM inference, planning, and coordination.
"""
from multiprocessing import Queue
import time
from pathlib import Path
from src.utils.logging_config import setup_logging

# Setup logging with rotating file handler
logger = setup_logging("AIBackend", "ai_backend.log")


class AIBackend:
    """AI Backend coordinator."""
    
    def __init__(self, command_queue: Queue, response_queue: Queue):
        """Initialize the AI backend."""
        self.command_queue = command_queue
        self.response_queue = response_queue
        self.running = False
        self.pending_plan = None
        self.pending_command_text = ""
        self.pending_confirmations = 0
        self.required_confirmations = 3
        
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
            from src.audio.wake_word import WakeWordDetector
            from src.core.config import config
            
            self.recorder = AudioRecorder()
            self.stt = SpeechToText(model_size="base")
            self.tts = TextToSpeech()
            self.wake_word = None

            self.required_confirmations = int(config.get("safety.dangerous_confirmation_count", 3) or 3)

            wake_word_enabled = bool(config.get("audio.wake_word_enabled", True))
            wake_word = config.get("audio.wake_word", "hey_jarvis")

            if wake_word_enabled:
                self.wake_word = WakeWordDetector(
                    wake_word=wake_word,
                    callback=self._on_wake_word_detected,
                )
                self.wake_word.start()
            
            logger.info("Audio components initialized")
        except Exception as e:
            logger.error(f"Error initializing audio: {e}")
            self.recorder = None
            self.stt = None
            self.tts = None
            self.wake_word = None

    def _on_wake_word_detected(self):
        """Handle wake word detection callback."""
        try:
            self.response_queue.put({
                "type": "event",
                "event": "wake_word_detected",
                "status": "success",
                "message": "Wake word detected"
            })
        except Exception as e:
            logger.error(f"Failed to emit wake word event: {e}")
    
    def _init_brain(self):
        """Initialize LLM and planning components."""
        try:
            from src.llm.planner import planner
            from src.memory.manager import memory
            from src.actions.executor import action_executor
            from src.plugins.plugin_manager import PluginManager
            from src.scheduler.task_scheduler import task_scheduler
            from src.watcher.file_watcher import file_watcher
            
            self.planner = planner
            self.memory = memory
            self.executor = action_executor
            
            # Initialize plugin system
            self.plugin_manager = PluginManager(skills_dir="./skills")
            self.plugin_manager.load_all_skills()
            
            # Initialize scheduler
            self.scheduler = task_scheduler
            
            # Initialize file watcher
            self.file_watcher = file_watcher
            
            logger.info("Brain components initialized")
        except Exception as e:
            logger.error(f"Error initializing brain: {e}")
            self.planner = None
            self.memory = None
            self.executor = None
            self.plugin_manager = None
            self.scheduler = None
            self.file_watcher = None
    
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
            if getattr(self, "wake_word", None):
                self.wake_word.stop()
            self.running = False
            logger.info("AI Backend stopped")

    def _handle_confirmation(self, text: str) -> dict:
        """Process confirmation/cancel flow for dangerous pending plans."""
        normalized = text.strip().lower()
        confirm_tokens = {"confirm", "yes", "proceed", "continue", "confirm execute"}
        cancel_tokens = {"cancel", "stop", "no", "abort"}

        if normalized in cancel_tokens:
            self.pending_plan = None
            self.pending_command_text = ""
            self.pending_confirmations = 0
            if self.tts:
                self.tts.speak("Dangerous task canceled.")
            return {
                "type": "response",
                "status": "success",
                "message": "Dangerous task canceled"
            }

        if normalized in confirm_tokens:
            self.pending_confirmations += 1
            remaining = self.required_confirmations - self.pending_confirmations

            if remaining > 0:
                if self.tts:
                    self.tts.speak(f"Confirmation {self.pending_confirmations} accepted. Say confirm {remaining} more time{'s' if remaining > 1 else ''}.")
                return {
                    "type": "response",
                    "status": "success",
                    "message": f"Confirmation {self.pending_confirmations}/{self.required_confirmations} received",
                    "awaiting_confirmation": True,
                    "remaining_confirmations": remaining
                }

            plan = self.pending_plan or []
            self.pending_plan = None
            self.pending_command_text = ""
            self.pending_confirmations = 0

            if self.tts:
                self.tts.speak(f"Final confirmation received. Executing {len(plan)} steps.")

            if self.executor and plan:
                result = self.executor.execute_plan(plan)
                success = result.get("success", False)
                message = f"Executed {result.get('successful_steps', 0)}/{result.get('total_steps', 0)} steps"
                return {
                    "type": "response",
                    "status": "success" if success else "partial",
                    "message": message,
                    "result": result
                }

            return {
                "type": "response",
                "status": "error",
                "message": "No pending plan to execute"
            }

        if self.tts:
            self.tts.speak("Please say confirm or cancel.")

        return {
            "type": "response",
            "status": "error",
            "message": "Awaiting confirmation. Say 'confirm' or 'cancel'.",
            "awaiting_confirmation": True,
            "remaining_confirmations": self.required_confirmations - self.pending_confirmations
        }

    def _process_transcribed_text(self, text: str) -> dict:
        """Route transcribed text through plugin/planner pipeline."""
        # Handle pending dangerous confirmation flow first.
        if self.pending_plan is not None:
            return self._handle_confirmation(text)

        # Store in memory
        if self.memory:
            self.memory.remember(
                content=f"User said: {text}",
                metadata={"type": "command"}
            )

        # First, check if a plugin can handle this
        plugin_result = None
        if self.plugin_manager:
            plugin_result = self.plugin_manager.execute_skill(text)

        if plugin_result:
            logger.info("Command handled by plugin")

            if self.tts:
                self.tts.speak(plugin_result.get("response", "Done"))

            return {
                "type": "response",
                "status": "success" if plugin_result.get("success") else "error",
                "message": plugin_result.get("response", ""),
                "plugin_data": plugin_result.get("data")
            }

        if self.planner:
            plan = self.planner.create_plan(text)

            if plan:
                needs_confirm = self.planner.needs_confirmation(plan)

                if needs_confirm:
                    self.pending_plan = plan
                    self.pending_command_text = text
                    self.pending_confirmations = 0

                    if self.tts:
                        self.tts.speak(
                            f"Dangerous action detected for '{text}'. "
                            f"Say confirm {self.required_confirmations} times to proceed, or say cancel."
                        )

                    return {
                        "type": "response",
                        "status": "success",
                        "message": (
                            f"Dangerous action requires {self.required_confirmations} confirmations"
                        ),
                        "needs_confirmation": True,
                        "awaiting_confirmation": True,
                        "remaining_confirmations": self.required_confirmations
                    }

                if self.tts:
                    self.tts.speak(f"Understood: {text}. Executing now.")

                return {
                    "type": "response",
                    "status": "success",
                    "message": f"Command: {text}",
                    "plan": plan,
                    "needs_confirmation": False
                }

            plan_error = getattr(self.planner, "last_error", "")
            user_message = "Could not create action plan"

            if "ollama model not found" in plan_error.lower() or "model not found" in plan_error.lower():
                user_message = "Ollama model missing. Run: ollama pull llama3.2"

            if self.tts:
                self.tts.speak(user_message)

            return {
                "type": "response",
                "status": "error",
                "message": user_message
            }

        if self.tts:
            self.tts.speak(f"I heard: {text}")

        return {
            "type": "response",
            "status": "success",
            "message": f"Transcribed: {text}"
        }
    
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

                        return self._process_transcribed_text(text)
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
                if self.tts:
                    self.tts.speak(f"Executing {len(plan)} steps.")

                result = self.executor.execute_plan(plan)
                
                success = result.get("success", False)
                message = f"Executed {result.get('successful_steps', 0)}/{result.get('total_steps', 0)} steps"
                
                # Speak result
                if self.tts:
                    if success:
                        self.tts.speak(f"Task completed successfully. {message}.")
                    else:
                        self.tts.speak(f"Task completed with some errors. {message}.")
                
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
        
        elif cmd_type == "file_drop":
            # Handle file drop event
            files = command.get("files", [])
            message = command.get("message", "")
            
            logger.info(f"Processing file drop: {len(files)} files")
            
            # Store in memory
            if self.memory:
                self.memory.remember(
                    content=f"User dropped files: {', '.join(files)}",
                    metadata={"type": "file_drop", "files": files}
                )
            
            # Speak acknowledgment
            if self.tts:
                self.tts.speak(f"I received {len(files)} file{'s' if len(files) > 1 else ''}. What would you like me to do with them?")
            
            return {
                "type": "response",
                "status": "success",
                "message": f"Received {len(files)} file(s)",
                "files": files
            }
        
        else:
            return {
                "type": "response",
                "status": "error",
                "message": f"Unknown command type: {cmd_type}"
            }
