"""
Speech-to-Text (STT) Module - The "Ears"
Uses faster-whisper for optimized local transcription.
"""
import logging
import wave
import tempfile
from pathlib import Path

logger = logging.getLogger("STT")


class SpeechToText:
    """Speech-to-Text engine using faster-whisper."""
    
    def __init__(self, model_size="base", device="auto"):
        """
        Initialize STT engine.
        
        Args:
            model_size: Model size (tiny, base, small, medium, large)
            device: Device to use (auto, cpu, cuda)
        """
        self.model_size = model_size
        self.device = device
        self.model = None
        
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model."""
        try:
            from faster_whisper import WhisperModel
            
            logger.info(f"Loading Whisper model: {self.model_size}")
            
            # Determine device
            device = self.device
            if device == "auto":
                try:
                    import torch
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                except:
                    device = "cpu"
            
            # Load model with optimizations
            self.model = WhisperModel(
                self.model_size,
                device=device,
                compute_type="int8" if device == "cpu" else "float16"
            )
            
            logger.info(f"Whisper model loaded on {device}")
            
        except ImportError:
            logger.error("faster-whisper not installed. Install with: pip install faster-whisper")
            self.model = None
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}")
            self.model = None
    
    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        if not self.model:
            logger.error("Whisper model not loaded")
            return ""
        
        try:
            logger.info(f"Transcribing audio: {audio_path}")
            
            # Transcribe
            segments, info = self.model.transcribe(
                audio_path,
                beam_size=5,
                vad_filter=True,  # Voice activity detection
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Combine segments
            text = " ".join([seg.text for seg in segments]).strip()
            
            logger.info(f"Transcription: {text}")
            return text
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""
    
    def transcribe_numpy(self, audio_data, sample_rate=16000) -> str:
        """
        Transcribe numpy array audio data.
        
        Args:
            audio_data: Numpy array of audio samples
            sample_rate: Sample rate (default: 16000)
            
        Returns:
            Transcribed text
        """
        if not self.model:
            return ""
        
        try:
            # Save to temporary WAV file
            temp_file = Path(tempfile.gettempdir()) / "temp_recording.wav"
            
            import numpy as np
            
            # Normalize
            if audio_data.dtype != np.int16:
                audio_data = (audio_data * 32767).astype(np.int16)
            
            # Save as WAV
            with wave.open(str(temp_file), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data.tobytes())
            
            # Transcribe
            result = self.transcribe(str(temp_file))
            
            # Cleanup
            temp_file.unlink(missing_ok=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Error transcribing numpy data: {e}")
            return ""
