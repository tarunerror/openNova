"""
Text-to-Speech (TTS) Module - The "Mouth"
Uses Microsoft Edge TTS for high-quality local synthesis.
"""
import asyncio
import os
import tempfile
from pathlib import Path
import logging

logger = logging.getLogger("TTS")


class TextToSpeech:
    """Text-to-Speech engine using Edge TTS."""
    
    def __init__(self, voice="en-US-AriaNeural"):
        """Initialize TTS engine."""
        self.voice = voice
        self.temp_dir = Path(tempfile.gettempdir()) / "ai_agent_tts"
        self.temp_dir.mkdir(exist_ok=True)
        
        try:
            import edge_tts
            self.edge_tts = edge_tts
            logger.info(f"TTS initialized with voice: {voice}")
        except ImportError:
            logger.error("edge-tts not installed. Install with: pip install edge-tts")
            self.edge_tts = None
    
    async def _synthesize_async(self, text: str) -> Path:
        """Synthesize speech asynchronously."""
        if not self.edge_tts:
            logger.error("Edge TTS not available")
            return None
        
        # Generate unique filename
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        output_file = self.temp_dir / f"speech_{text_hash}.mp3"
        
        # Synthesize
        communicate = self.edge_tts.Communicate(text, self.voice)
        await communicate.save(str(output_file))
        
        return output_file
    
    def synthesize(self, text: str) -> Path:
        """Synthesize speech and return path to audio file."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self._synthesize_async(text))
    
    def speak(self, text: str):
        """Synthesize and play speech."""
        logger.info(f"Speaking: {text}")
        
        audio_file = self.synthesize(text)
        if audio_file and audio_file.exists():
            self._play_audio(audio_file)
    
    def _play_audio(self, audio_path: Path):
        """Play audio file using system default player."""
        try:
            from playsound import playsound
            playsound(str(audio_path), block=True)
                
        except Exception as e:
            logger.error(f"Error playing audio with playsound: {e}")
            try:
                import platform
                system = platform.system()

                if system == "Windows":
                    os.startfile(str(audio_path))
                elif system == "Darwin":  # macOS
                    os.system(f"afplay {audio_path}")
                else:  # Linux
                    os.system(f"mpg123 {audio_path}")
            except Exception as fallback_error:
                logger.error(f"Fallback audio playback failed: {fallback_error}")
    
    @staticmethod
    def list_voices():
        """List available voices."""
        try:
            import edge_tts
            loop = asyncio.get_event_loop()
            voices = loop.run_until_complete(edge_tts.list_voices())
            return voices
        except:
            return []
