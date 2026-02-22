import queue
import threading
import numpy as np

MODEL_SIZE = "medium"


class TranscriptionWorker:
    """Loads faster-whisper and processes audio chunks from a queue."""

    def __init__(self, on_result):
        self.on_result = on_result
        self._queue = queue.Queue()
        self._thread = None
        self._running = False
        self._model = None

    def load_model(self, progress_callback=None):
        from faster_whisper import WhisperModel

        if progress_callback:
            progress_callback("Cargando modelo Whisper medium...")

        try:
            self._model = WhisperModel(
                MODEL_SIZE,
                device="cuda",
                compute_type="int8_float16",
            )
            if progress_callback:
                progress_callback("Modelo listo (CUDA)")
        except Exception:
            # Fallback to CPU if CUDA is not available
            self._model = WhisperModel(
                MODEL_SIZE,
                device="cpu",
                compute_type="int8",
            )
            if progress_callback:
                progress_callback("Modelo listo (CPU)")

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        self._queue.put(None)  # sentinel to unblock the worker

    def enqueue(self, audio: np.ndarray, source: str):
        self._queue.put((audio, source))

    def _worker(self):
        while self._running:
            item = self._queue.get()
            if item is None:
                break
            audio, source = item
            try:
                segments, _ = self._model.transcribe(
                    audio,
                    language="es",
                    beam_size=5,
                    vad_filter=True,
                    vad_parameters={"min_silence_duration_ms": 500},
                )
                text = " ".join(seg.text.strip() for seg in segments).strip()
                if text:
                    self.on_result(text, source)
            except Exception as e:
                print(f"[ERROR] Transcripcion: {e}")
