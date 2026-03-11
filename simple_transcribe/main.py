import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import sounddevice as sd
import typer
from notifypy import Notify
from openai import OpenAI
from scipy.io.wavfile import write

app = typer.Typer(help="voice-input - record and transcribe audio to clipboard", add_completion=False)

SAMPLERATE = 16000
CHANNELS = 1
CHUNK_DURATION_SEC = 5 * 60  # 5 minutes


def transcribe_file(client: OpenAI, file_path: str, language: str | None = None) -> str:
    print(f"Sending to Whisper API... {file_path}")
    with open(file_path, "rb") as f:
        kwargs = {"model": "gpt-4o-transcribe", "file": f}
        if language is not None:
            kwargs["language"] = language
        result = client.audio.transcriptions.create(**kwargs)
    return result.text


def copy_to_clipboard(text: str):
    try:
        subprocess.run(["wl-copy"], input=text, text=True, check=True)
        print("Copied to clipboard")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Could not copy to clipboard (wl-copy not found)", file=sys.stderr)


def send_notification(title: str, body: str):
    try:
        notification = Notify()
        notification.title = title
        notification.message = body
        notification.send()
    except Exception:
        pass


def record() -> list[Path]:
    print("Starting recording (Ctrl+D to stop)...")

    audio_frames: list[np.ndarray] = []

    def callback(indata, _frames, _time, status):
        if status:
            print(status, file=sys.stderr)
        audio_frames.append(indata.copy())
        normalized = indata.astype(np.float32) / 32768.0
        rms = np.sqrt(max(0, np.mean(normalized**2)))
        db = 20 * np.log10(rms) if rms > 0 else -60
        bar = "#" * max(0, int((db + 60) / 2))
        print(f"\r  {bar:<30}", end="", flush=True)

    try:
        with sd.InputStream(
            samplerate=SAMPLERATE, channels=CHANNELS, dtype="int16", callback=callback
        ):
            while True:
                try:
                    input()
                except EOFError:
                    print()
                    break
    except KeyboardInterrupt:
        print("\nRecording stopped")
        sys.exit(0)

    if not audio_frames:
        print("No audio recorded.", file=sys.stderr)
        sys.exit(1)

    audio = np.concatenate(audio_frames, axis=0)

    chunk_size = CHUNK_DURATION_SEC * SAMPLERATE
    num_chunks = int(np.ceil(len(audio) / chunk_size))
    chunk_files: list[Path] = []

    os.makedirs("audio", exist_ok=True)

    for i in range(num_chunks):
        start = int(i * chunk_size)
        end = int(min((i + 1) * chunk_size, len(audio)))
        path = Path("audio") / f"chunk_{i:03d}.wav"
        write(str(path), SAMPLERATE, audio[start:end])
        chunk_files.append(path)
        print(f"Saved: {path}")

    return chunk_files


@app.command()
def main(
    language: str | None = typer.Option(
        None, "--language", "--lang", "-l", help="Language code for transcription (e.g. en, ja)"
    ),
):
    """Record audio from microphone and transcribe to clipboard."""
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    files = record()

    all_text = ""
    for f in files:
        text = transcribe_file(client, str(f), language)
        print(text)
        all_text += text + "\n"

    all_text = all_text.strip()

    copy_to_clipboard(all_text)
    send_notification("Transcription Complete", "Copied to clipboard")


def main_cli():
    app()


if __name__ == "__main__":
    app()
