# Transcriptor

> Aplicación de escritorio para transcribir llamadas en tiempo real. Captura el micrófono y el audio del sistema simultáneamente y convierte todo a texto usando Whisper de forma local.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white"/>
  <img src="https://img.shields.io/badge/NVIDIA_CUDA-76B900?style=for-the-badge&logo=nvidia&logoColor=white"/>
  <img src="https://img.shields.io/badge/Whisper-412991?style=for-the-badge&logo=openai&logoColor=white"/>
  <img src="https://img.shields.io/badge/faster--whisper-FF6B35?style=for-the-badge&logo=python&logoColor=white"/>
</p>

---

## Características

- **Micrófono** — transcribe lo que dices tú
- **Audio del sistema** — transcribe lo que escuchas (Zoom, Teams, YouTube, etc.) via WASAPI loopback
- **100% local** — sin internet, sin APIs externas, sin costo
- **Español** — optimizado con modelo `medium` fijo en `language=es`
- **GPU accelerado** — usa CUDA en RTX 3050+ para transcripción rápida
- **Exportar** — guarda la transcripción completa a `.txt`

---

## Instalación

### 1. Requisitos previos
- Python 3.10+
- NVIDIA GPU con CUDA 12 (opcional pero recomendado)

### 2. Entorno virtual

```bash
python -m venv venv
source venv/Scripts/activate  # Windows Git Bash
# o: venv\Scripts\activate.bat  # CMD
```

### 3. Dependencias

```bash
pip install -r requirements.txt
```

### 4. Soporte CUDA (RTX 3050 / CUDA 12)

```bash
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

> Si no tienes GPU NVIDIA, la app corre igual en CPU (más lento).

---

## Uso

```bash
python main.py
```

1. La app carga el modelo Whisper `medium` (~800MB, se descarga automáticamente la primera vez)
2. Presiona **▶ Iniciar** para comenzar la captura
3. Las transcripciones aparecen en tiempo real:
   - <span style="color:#4FC3F7">**[MIC]**</span> — lo que dices tú
   - <span style="color:#A5D6A7">**[SISTEMA]**</span> — lo que escuchas (Zoom, etc.)
4. Presiona **■ Detener** para parar
5. Usa **Guardar .txt** para exportar

---

## Tecnologías

| Librería | Uso |
|---|---|
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Motor de transcripción (CTranslate2) |
| [pyaudiowpatch](https://github.com/s0d3s/PyAudioWPatch) | Captura WASAPI loopback (audio del sistema) |
| [sounddevice](https://python-sounddevice.readthedocs.io/) | Captura de micrófono |
| [customtkinter](https://github.com/TomSchimansky/CustomTkinter) | UI moderna |
| [scipy](https://scipy.org/) | Resampleo de audio |

---

## Arquitectura

```
Mic thread (sounddevice)         ─┐
                                   ├─► AudioBuffer (4s) ─► TranscriptionWorker ─► UI
Loopback thread (pyaudiowpatch)  ─┘        (numpy)          (faster-whisper CUDA)
```
