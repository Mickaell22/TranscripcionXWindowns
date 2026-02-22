import threading

from transcriber.audio_capture import AudioCapture
from transcriber.transcription import TranscriptionWorker
from ui.app import App


def main():
    worker = TranscriptionWorker(on_result=None)
    capture = AudioCapture(on_chunk_ready=None)

    def on_result(text, source):
        app.after(0, lambda: app.append_text(text, source))

    def on_start():
        capture.start()

    def on_stop():
        capture.stop()

    worker.on_result = on_result
    capture.on_chunk_ready = worker.enqueue

    app = App(on_start=on_start, on_stop=on_stop)

    capture.on_waveform = lambda audio, source: app.after(
        0, lambda a=audio, s=source: app.push_waveform(a, s)
    )

    def load_model():
        worker.load_model(
            progress_callback=lambda msg: app.after(
                0, lambda m=msg: app.set_status(f"● {m}", "#F0A500")
            )
        )
        worker.start()
        app.after(0, app.set_ready)

    threading.Thread(target=load_model, daemon=True).start()

    app.mainloop()
    worker.stop()


if __name__ == "__main__":
    main()
