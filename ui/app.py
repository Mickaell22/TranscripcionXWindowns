from datetime import datetime
from tkinter import filedialog
import tkinter as tk

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

MIC_COLOR = "#4FC3F7"
SISTEMA_COLOR = "#A5D6A7"
TIMESTAMP_COLOR = "#555555"


class App(ctk.CTk):
    def __init__(self, on_start, on_stop):
        super().__init__()
        self.on_start = on_start
        self.on_stop = on_stop
        self.is_running = False

        # Almacena los datos raw para exportar sin logs
        # Cada entrada: {"source": "MIC"|"SISTEMA", "text": "..."}
        self._entries: list[dict] = []

        self.title("Transcriptor")
        self.geometry("960x680")
        self.minsize(800, 500)

        self._build_ui()

    # ------------------------------------------------------------------ #
    #  UI                                                                  #
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        # ---- header ----
        header = ctk.CTkFrame(self, height=56, corner_radius=0, fg_color=("#1a1a2e", "#1a1a2e"))
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="  Transcriptor",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#E0E0E0",
        ).pack(side="left", padx=16)

        self.status_label = ctk.CTkLabel(
            header,
            text="● Cargando modelo...",
            text_color="#F0A500",
            font=ctk.CTkFont(size=12),
        )
        self.status_label.pack(side="right", padx=20)

        # ---- legend ----
        legend = ctk.CTkFrame(self, height=28, corner_radius=0, fg_color="transparent")
        legend.pack(fill="x", padx=16, pady=(6, 0))

        ctk.CTkLabel(legend, text="■ MIC", text_color=MIC_COLOR,
                     font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 16))
        ctk.CTkLabel(legend, text="■ SISTEMA", text_color=SISTEMA_COLOR,
                     font=ctk.CTkFont(size=11)).pack(side="left")

        # ---- transcript ----
        self.textbox = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="word",
            state="disabled",
            corner_radius=8,
        )
        self.textbox.pack(fill="both", expand=True, padx=16, pady=8)

        self.textbox.tag_config("MIC", foreground=MIC_COLOR)
        self.textbox.tag_config("SISTEMA", foreground=SISTEMA_COLOR)
        self.textbox.tag_config("ts", foreground=TIMESTAMP_COLOR)

        # ---- fila 1: control ----
        row1 = ctk.CTkFrame(self, height=48, corner_radius=0, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(0, 4))
        row1.pack_propagate(False)

        self.toggle_btn = ctk.CTkButton(
            row1, text="▶  Iniciar", width=140, height=36,
            command=self._toggle, state="disabled",
        )
        self.toggle_btn.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            row1, text="Limpiar", width=90, height=36,
            fg_color="transparent", border_width=1,
            command=self._clear,
        ).pack(side="left")

        # ---- fila 2: copiar / guardar ----
        row2 = ctk.CTkFrame(self, height=48, corner_radius=0, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 10))
        row2.pack_propagate(False)

        # separador visual
        ctk.CTkLabel(row2, text="Copiar:", font=ctk.CTkFont(size=11),
                     text_color="#888").pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            row2, text="MIC", width=72, height=32,
            fg_color="transparent", border_width=1,
            border_color=MIC_COLOR, text_color=MIC_COLOR,
            command=lambda: self._copy("MIC"),
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            row2, text="SISTEMA", width=88, height=32,
            fg_color="transparent", border_width=1,
            border_color=SISTEMA_COLOR, text_color=SISTEMA_COLOR,
            command=lambda: self._copy("SISTEMA"),
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            row2, text="Conversación", width=110, height=32,
            fg_color="transparent", border_width=1,
            command=lambda: self._copy(None),
        ).pack(side="left", padx=(0, 20))

        ctk.CTkLabel(row2, text="Guardar:", font=ctk.CTkFont(size=11),
                     text_color="#888").pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            row2, text="MIC", width=72, height=32,
            fg_color="transparent", border_width=1,
            border_color=MIC_COLOR, text_color=MIC_COLOR,
            command=lambda: self._save("MIC"),
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            row2, text="SISTEMA", width=88, height=32,
            fg_color="transparent", border_width=1,
            border_color=SISTEMA_COLOR, text_color=SISTEMA_COLOR,
            command=lambda: self._save("SISTEMA"),
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            row2, text="Conversación", width=110, height=32,
            fg_color="transparent", border_width=1,
            command=lambda: self._save(None),
        ).pack(side="left")

    # ------------------------------------------------------------------ #
    #  Helpers de datos                                                    #
    # ------------------------------------------------------------------ #

    def _build_clean_text(self, source_filter: str | None) -> str:
        """
        Construye texto limpio (sin timestamps ni logs) para copiar/guardar.
        - source_filter="MIC" o "SISTEMA": solo esa fuente, texto plano.
        - source_filter=None: conversación completa con etiqueta mínima (MIC: / SISTEMA:).
        """
        if source_filter:
            lines = [e["text"] for e in self._entries if e["source"] == source_filter]
            return "\n".join(lines)
        else:
            lines = [f"{e['source']}: {e['text']}" for e in self._entries]
            return "\n".join(lines)

    # ------------------------------------------------------------------ #
    #  Callbacks                                                           #
    # ------------------------------------------------------------------ #

    def _toggle(self):
        if not self.is_running:
            self.is_running = True
            self.toggle_btn.configure(text="■  Detener", fg_color="#C62828")
            self.set_status("● Grabando", "#66BB6A")
            self.on_start()
        else:
            self.is_running = False
            self.toggle_btn.configure(text="▶  Iniciar", fg_color=("#3B8ED0", "#1F6AA5"))
            self.set_status("● Detenido", "#EF5350")
            self.on_stop()

    def _clear(self):
        self._entries.clear()
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")

    def _copy(self, source_filter: str | None):
        text = self._build_clean_text(source_filter)
        if not text:
            return
        self.clipboard_clear()
        self.clipboard_append(text)

    def _save(self, source_filter: str | None):
        text = self._build_clean_text(source_filter)
        if not text:
            return
        if source_filter:
            default_name = f"transcripcion_{source_filter.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        else:
            default_name = f"transcripcion_completa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt")],
            initialfile=default_name,
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def append_text(self, text: str, source: str):
        # Guardar raw para exportar
        self._entries.append({"source": source, "text": text})

        # Mostrar en UI con logs (timestamp + fuente coloreada)
        ts = datetime.now().strftime("%H:%M:%S")
        self.textbox.configure(state="normal")
        self.textbox.insert("end", f"[{ts}] ", "ts")
        self.textbox.insert("end", f"[{source}] ", source)
        self.textbox.insert("end", f"{text}\n")
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def set_status(self, text: str, color: str = "#E0E0E0"):
        self.status_label.configure(text=text, text_color=color)

    def set_ready(self):
        self.toggle_btn.configure(state="normal")
        self.set_status("● Listo", "#66BB6A")
