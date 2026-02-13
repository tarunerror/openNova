"""
Audio Recorder - Captures microphone input.
"""
import logging
import threading
import numpy as np

logger = logging.getLogger("AudioRecorder")


class AudioRecorder:
    """Records audio from microphone."""
    
    def __init__(self, sample_rate=16000, channels=1, chunk_size=1024):
        """
        Initialize audio recorder.
        
        Args:
            sample_rate: Sample rate in Hz
            channels: Number of audio channels
            chunk_size: Size of audio chunks
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        
        self.is_recording = False
        self.frames = []
        self.stream = None
        self.audio = None
        
        self._initialize_audio()
    
    def _initialize_audio(self):
        """Initialize PyAudio."""
        try:
            import pyaudio
            self.audio = pyaudio.PyAudio()
            logger.info("Audio system initialized")
        except ImportError:
            logger.error("PyAudio not installed. Install with: pip install pyaudio")
            self.audio = None
        except Exception as e:
            logger.error(f"Error initializing audio: {e}")
            self.audio = None
    
    def start_recording(self):
        """Start recording audio."""
        if not self.audio:
            logger.error("Audio system not available")
            return False
        
        if self.is_recording:
            logger.warning("Already recording")
            return False
        
        try:
            import pyaudio
            
            self.frames = []
            self.is_recording = True
            
            # Open stream
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.stream.start_stream()
            logger.info("Recording started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            self.is_recording = False
            return False
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio stream."""
        import pyaudio
        
        if self.is_recording:
            self.frames.append(in_data)
        
        return (in_data, pyaudio.paContinue)
    
    def stop_recording(self) -> np.ndarray:
        """
        Stop recording and return audio data.
        
        Returns:
            Numpy array of audio samples
        """
        if not self.is_recording:
            logger.warning("Not recording")
            return np.array([])
        
        try:
            self.is_recording = False
            
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            
            # Convert frames to numpy array
            if self.frames:
                audio_data = b''.join(self.frames)
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                logger.info(f"Recording stopped. Captured {len(audio_array)} samples")
                return audio_array
            else:
                logger.warning("No audio data captured")
                return np.array([])
                
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            return np.array([])
    
    def record_duration(self, duration_seconds: float) -> np.ndarray:
        """
        Record for a specific duration.
        
        Args:
            duration_seconds: Duration to record in seconds
            
        Returns:
            Numpy array of audio samples
        """
        import time
        
        if self.start_recording():
            time.sleep(duration_seconds)
            return self.stop_recording()
        else:
            return np.array([])
    
    def cleanup(self):
        """Clean up audio resources."""
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
        
        if self.audio:
            try:
                self.audio.terminate()
            except:
                pass
        
        logger.info("Audio recorder cleaned up")
    
    def __del__(self):
        """Destructor."""
        self.cleanup()
