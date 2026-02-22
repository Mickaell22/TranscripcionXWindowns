from datetime import datetime
from tkinter import filedialog

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

MIC_COLOR = "#4FC3F7"       # azul claro
SISTEMA_COLOR = "#A5D6A7"   # verde claro
TIMESTAMP_COLOR = "#555555"


class App(ctk.CTk):
    def __init__(self, on_start, on_stop):
        super().__init__()
        self.on_start = on_start
        self.on_stop = on_stop
        self.is_running = False

        self.title("Transcriptor")
        self.geometry("960x620")
        self.minsize(720, 440)

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

        # ---- bottom bar ----
        bottom = ctk.CTkFrame(self, height=56, corner_radius=0, fg_color="transparent")
        bottom.pack(fill="x", padx=16, pady=(0, 10))
        bottom.pack_propagate(False)

        self.toggle_btn = ctk.CTkButton(
            bottom,
            text="▶  Iniciar",
            width=140,
            height=38,
            command=self._toggle,
            state="disabled",
        )
        self.toggle_btn.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            bottom,
            text="Limpiar",
            width=100,
            height=38,
            fg_color="transparent",
            border_width=1,
            command=self._clear,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            bottom,
            text="Guardar .txt",
            width=120,
            height=38,
            fg_color="transparent",
            border_width=1,
            command=self._save,
        ).pack(side="left")

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
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")

    def _save(self):
        text = self.textbox.get("1.0", "end").strip()
        if not text:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt")],
            initialfile=f"transcripcion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)

    # ------------------------------------------------------------------ #
    #  Public API (called from other threads via app.after)               #
    # ------------------------------------------------------------------ #

    def append_text(self, text: str, source: str):
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
