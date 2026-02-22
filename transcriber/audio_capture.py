import threading
from math import gcd

import numpy as np
import sounddevice as sd

from .buffer import AudioBuffer, SAMPLE_RATE


class AudioCapture:
    """Manages two capture threads: microphone and WASAPI loopback."""

    def __init__(self, on_chunk_ready):
        self.on_chunk_ready = on_chunk_ready
        self._running = False
        # Usar lambda para que siempre llame a self.on_chunk_ready actual,
        # no la referencia que se pase al constructor (puede ser None al inicio)
        self._mic_buffer = AudioBuffer("MIC", lambda c, s: self.on_chunk_ready(c, s))
        self._sys_buffer = AudioBuffer("SISTEMA", lambda c, s: self.on_chunk_ready(c, s))
        self._mic_stream = None
        self._pyaudio = None
        self._loopback_stream = None

    def start(self):
        self._running = True
        self._start_mic()
        self._start_loopback()

    def stop(self):
        self._running = False
        if self._mic_stream:
            self._mic_stream.stop()
            self._mic_stream.close()
            self._mic_stream = None
        if self._loopback_stream:
            self._loopback_stream.stop_stream()
            self._loopback_stream.close()
            self._loopback_stream = None
        if self._pyaudio:
            self._pyaudio.terminate()
            self._pyaudio = None
        self._mic_buffer.flush()
        self._sys_buffer.flush()

    def _start_mic(self):
        # Capture at native device rate and resample to 16000Hz
        device_info = sd.query_devices(kind="input")
        native_rate = int(device_info["default_samplerate"])

        def callback(indata, frames, time, status):
            if not self._running:
                return
            audio = indata[:, 0].astype(np.float32)
            if native_rate != SAMPLE_RATE:
                from scipy.signal import resample_poly
                g = gcd(SAMPLE_RATE, native_rate)
                audio = resample_poly(audio, SAMPLE_RATE // g, native_rate // g)
            self._mic_buffer.push(audio.astype(np.float32))

        self._mic_stream = sd.InputStream(
            samplerate=native_rate,
            channels=1,
            dtype="float32",
            callback=callback,
            blocksize=4096,
        )
        self._mic_stream.start()
        print(f"[OK] Mic activo @ {native_rate}Hz -> resampleando a {SAMPLE_RATE}Hz")

    def _start_loopback(self):
        try:
            import pyaudiowpatch as pyaudio
        except ImportError:
            print("[WARN] pyaudiowpatch no instalado. Audio del sistema desactivado.")
            return

        self._pyaudio = pyaudio.PyAudio()

        try:
            wasapi_info = self._pyaudio.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_speakers = self._pyaudio.get_device_info_by_index(
                wasapi_info["defaultOutputDevice"]
            )

            # Si el dispositivo por defecto ya es loopback, usarlo directamente
            if not default_speakers.get("isLoopbackDevice", False):
                loopback_device = None
                for loopback in self._pyaudio.get_loopback_device_info_generator():
                    if default_speakers["name"] in loopback["name"]:
                        loopback_device = loopback
                        break
                if loopback_device is None:
                    print("[WARN] No se encontro dispositivo loopback WASAPI.")
                    return
            else:
                loopback_device = default_speakers

            device_rate = int(loopback_device["defaultSampleRate"])
            channels = min(int(loopback_device["maxInputChannels"]), 2)

            def loopback_callback(in_data, frame_count, time_info, status):
                if not self._running:
                    return (None, pyaudio.paComplete)

                audio = np.frombuffer(in_data, dtype=np.float32).copy()

                if channels == 2:
                    audio = audio.reshape(-1, 2).mean(axis=1)

                if device_rate != SAMPLE_RATE:
                    from scipy.signal import resample_poly
                    g = gcd(SAMPLE_RATE, device_rate)
                    audio = resample_poly(audio, SAMPLE_RATE // g, device_rate // g)

                self._sys_buffer.push(audio.astype(np.float32))
                return (None, pyaudio.paContinue)

            self._loopback_stream = self._pyaudio.open(
                format=pyaudio.paFloat32,
                channels=channels,
                rate=device_rate,
                input=True,
                input_device_index=int(loopback_device["index"]),
                frames_per_buffer=4096,
                stream_callback=loopback_callback,
            )
            self._loopback_stream.start_stream()
            print(f"[OK] Loopback activo: {loopback_device['name']} @ {device_rate}Hz")

        except Exception as e:
            print(f"[ERROR] Loopback WASAPI: {e}")
