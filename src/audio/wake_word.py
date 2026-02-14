"""
Wake word detection using openWakeWord.
"""
import logging
import time
from threading import Thread
from typing import Callable, Optional

import numpy as np

logger = logging.getLogger("WakeWord")


class WakeWordDetector:
    """Detects wake words in microphone audio stream."""

    def __init__(
        self,
        wake_word: str = "hey_jarvis",
        callback: Optional[Callable] = None,
        threshold: float = 0.5,
        cooldown_seconds: float = 2.0,
    ):
        self.wake_word = wake_word
        self.callback = callback
        self.threshold = threshold
        self.cooldown_seconds = cooldown_seconds

        self.running = False
        self.detection_thread = None

        self.model = None
        self.pyaudio = None
        self.audio_stream = None
        self._last_trigger_ts = 0.0
        self.model_id = wake_word

        self.available = self._initialize_backend()

    def _initialize_backend(self) -> bool:
        try:
            import pyaudio
            from openwakeword.model import Model
            from openwakeword import utils as oww_utils

            self.pyaudio = pyaudio
            requested = (self.wake_word or "").strip().lower().replace(" ", "_")
            alias_map = {
                "hey_agent": "hey_jarvis",
                "hey_assistant": "hey_jarvis",
                "hey_jarvis": "hey_jarvis",
                "alexa": "alexa",
            }
            self.model_id = alias_map.get(requested, requested)

            try:
                self.model = Model(wakeword_models=[self.model_id], inference_framework="onnx")
                logger.info(f"Wake word model loaded: {self.model_id}")
            except Exception as model_error:
                logger.warning(f"Requested wake word model '{self.model_id}' unavailable: {model_error}")
                try:
                    logger.info("Attempting to download openWakeWord model assets...")
                    oww_utils.download_models()
                    self.model = Model(wakeword_models=[self.model_id], inference_framework="onnx")
                    logger.info(f"Wake word model loaded after download: {self.model_id}")
                except Exception:
                    self.model = Model(inference_framework="onnx")
                    self.model_id = ""
                    logger.info("Wake word model loaded with default openWakeWord model set")

            return True
        except Exception as error:
            logger.warning(f"Wake word detector unavailable: {error}")
            return False

    def start(self):
        """Start wake word detection loop in a background thread."""
        if self.running:
            logger.warning("Wake word detector already running")
            return

        if not self.available:
            logger.warning("Wake word detector cannot start because dependencies are unavailable")
            return

        self.running = True
        self.detection_thread = Thread(target=self._run_loop, name="WakeWordThread", daemon=True)
        self.detection_thread.start()
        logger.info("Wake word detector started")

    def _run_loop(self):
        chunk_size = 1280

        try:
            pa = self.pyaudio.PyAudio()
            self.audio_stream = pa.open(
                format=self.pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=chunk_size,
            )

            logger.info("Wake word microphone stream opened")

            while self.running:
                raw_data = self.audio_stream.read(chunk_size, exception_on_overflow=False)
                audio = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0

                prediction = self.model.predict(audio)
                score = self._extract_score(prediction)

                if score >= self.threshold and (time.time() - self._last_trigger_ts) >= self.cooldown_seconds:
                    self._last_trigger_ts = time.time()
                    logger.info(f"Wake word detected (score={score:.3f})")
                    if self.callback:
                        try:
                            self.callback()
                        except Exception as callback_error:
                            logger.error(f"Wake word callback failed: {callback_error}")

        except Exception as error:
            logger.error(f"Wake word loop error: {error}")
        finally:
            self._cleanup_stream()

    def _extract_score(self, prediction) -> float:
        if not prediction:
            return 0.0

        if isinstance(prediction, dict):
            if self.model_id and self.model_id in prediction:
                value = prediction[self.model_id]
                if isinstance(value, (list, tuple)) and value:
                    return float(value[-1])
                return float(value)

            normalized_prediction = {
                str(key).lower(): value
                for key, value in prediction.items()
            }
            wake_word_key = (self.wake_word or "").lower().replace(" ", "_")
            if wake_word_key in normalized_prediction:
                value = normalized_prediction[wake_word_key]
                if isinstance(value, (list, tuple)) and value:
                    return float(value[-1])
                return float(value)

            first_value = next(iter(prediction.values()))
            if isinstance(first_value, (list, tuple)) and first_value:
                return float(first_value[-1])
            return float(first_value)

        if isinstance(prediction, (list, tuple)) and prediction:
            return float(prediction[-1])

        try:
            return float(prediction)
        except Exception:
            return 0.0

    def _cleanup_stream(self):
        try:
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
        except Exception:
            pass
        finally:
            self.audio_stream = None

    def stop(self):
        """Stop wake word detection."""
        if not self.running:
            return

        self.running = False
        if self.detection_thread and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=2)
        self._cleanup_stream()
        logger.info("Wake word detector stopped")

    def is_running(self) -> bool:
        return self.running

    def __del__(self):
        self.stop()
