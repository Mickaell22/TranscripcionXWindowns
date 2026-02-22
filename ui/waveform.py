import collections
import tkinter as tk

import numpy as np
import customtkinter as ctk


class WaveformWidget(ctk.CTkFrame):
    _BAR_COUNT = 80
    _UPDATE_MS = 50

    def __init__(self, parent, color: str, label: str, **kwargs):
        kwargs.setdefault("fg_color", "#0d0d1a")
        kwargs.setdefault("corner_radius", 8)
        super().__init__(parent, **kwargs)

        self._color = color
        self._buffer = collections.deque(maxlen=8192)
        self._active = False

        ctk.CTkLabel(
            self,
            text=label,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=color,
        ).pack(anchor="w", padx=8, pady=(4, 0))

        self._canvas = tk.Canvas(
            self, height=52, bg="#0d0d1a", highlightthickness=0
        )
        self._canvas.pack(fill="both", expand=True, padx=6, pady=(2, 6))

        self._animate()

    def push_audio(self, audio: np.ndarray):
        self._buffer.extend(audio.tolist())
        self._active = True

    def clear(self):
        self._buffer.clear()
        self._active = False

    def _animate(self):
        canvas = self._canvas
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        canvas.delete("all")

        cy = h // 2 if h > 1 else 26

        if w <= 1:
            self.after(self._UPDATE_MS, self._animate)
            return

        # linea base
        canvas.create_line(0, cy, w, cy, fill="#1a1a2e", width=1)

        samples = list(self._buffer)
        if samples and self._active:
            n = self._BAR_COUNT
            bar_w = max(1, (w - n) // n)
            chunk_size = max(1, len(samples) // n)

            amps = []
            for i in range(n):
                sl = samples[i * chunk_size: (i + 1) * chunk_size]
                amps.append(float(np.max(np.abs(sl))) if sl else 0.0)

            peak = max(amps) if max(amps) > 0.01 else 0.01
            scale = (cy - 2) / peak

            for i, amp in enumerate(amps):
                x = i * (bar_w + 1)
                bh = max(1, int(amp * scale))
                # barra simetrica top/bottom
                canvas.create_rectangle(
                    x, cy - bh,
                    x + bar_w, cy + bh,
                    fill=self._color, outline="",
                )

        self.after(self._UPDATE_MS, self._animate)
