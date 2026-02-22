import os
import sys
import queue
import threading
import numpy as np

MODEL_SIZE = "medium"


def _add_cuda_to_path():
    """Agrega los DLLs de CUDA instalados via pip al PATH de Windows.
    sys.executable = venv/Scripts/python.exe → subimos a venv/ para encontrar Lib/site-packages.
    """
    scripts_dir = os.path.dirname(sys.executable)          # venv/Scripts
    venv_dir = os.path.dirname(scripts_dir)                 # venv/
    nvidia_base = os.path.join(venv_dir, "Lib", "site-packages", "nvidia")
    if not os.path.isdir(nvidia_base):
        return
    for pkg in os.listdir(nvidia_base):
        bin_dir = os.path.join(nvidia_base, pkg, "bin")
        if os.path.isdir(bin_dir) and bin_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
            print(f"[CUDA] PATH += {bin_dir}")


class TranscriptionWorker:
    """Loads faster-whisper and processes audio chunks from a queue."""

    def __init__(self, on_result):
        self.on_result = on_result
        self._queue = queue.Queue()
        self._thread = None
        self._running = False
        self._model = None

    def load_model(self, progress_callback=None):
        _add_cuda_to_path()
        from faster_whisper import WhisperModel

        if progress_callback:
            progress_callback("Cargando modelo Whisper medium...")

        try:
            self._model = WhisperModel(
                MODEL_SIZE,
                device="cuda",
                compute_type="float16",
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

    @staticmethod
    def _denoise(audio: np.ndarray) -> np.ndarray:
        """Reduccion de ruido espectral estatico para el microfono (noisereduce)."""
        try:
            import noisereduce as nr
            return nr.reduce_noise(
                y=audio,
                sr=16000,
                stationary=True,   # ruido constante: ventilador, AC, etc.
                prop_decrease=0.75, # agresividad: 0=nada, 1=maximo
            )
        except Exception as e:
            print(f"[WARN] Denoise fallo, usando audio original: {e}")
            return audio

    def _worker(self):
        while self._running:
            item = self._queue.get()
            if item is None:
                break
            audio, source = item
            try:
                if source == "MIC":
                    audio = self._denoise(audio)

                segments, _ = self._model.transcribe(
                    audio,
                    language="es",
                    beam_size=5,
                    vad_filter=True,
                    vad_parameters=dict(
                        min_silence_duration_ms=2000,
                        speech_pad_ms=400,
                    ),
                )
                # segments es un generador — consumirlo completo para ejecutar la transcripcion
                text = " ".join(seg.text.strip() for seg in segments).strip()
                if text:
                    self.on_result(text, source)
            except Exception as e:
                print(f"[ERROR] Transcripcion: {e}")
