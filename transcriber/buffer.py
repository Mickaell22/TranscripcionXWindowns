import threading
import numpy as np

SAMPLE_RATE = 16000
CHUNK_SECONDS = 4
CHUNK_SAMPLES = SAMPLE_RATE * CHUNK_SECONDS


class AudioBuffer:
    """Accumulates raw audio samples and fires a callback every CHUNK_SECONDS."""

    def __init__(self, source: str, on_chunk_ready):
        self.source = source
        self.on_chunk_ready = on_chunk_ready
        self._buffer = np.array([], dtype=np.float32)
        self._lock = threading.Lock()

    def push(self, audio: np.ndarray):
        with self._lock:
            self._buffer = np.concatenate([self._buffer, audio])
            while len(self._buffer) >= CHUNK_SAMPLES:
                chunk = self._buffer[:CHUNK_SAMPLES].copy()
                self._buffer = self._buffer[CHUNK_SAMPLES:]
                self.on_chunk_ready(chunk, self.source)

    def flush(self):
        """Send whatever remains (at least 1 second) on stop."""
        with self._lock:
            if len(self._buffer) >= SAMPLE_RATE:
                chunk = self._buffer.copy()
                self._buffer = np.array([], dtype=np.float32)
                self.on_chunk_ready(chunk, self.source)
