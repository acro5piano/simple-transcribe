# simple-transcribe

A dead simple speech to text using gpt-4o-transcribe.

Records audio from your microphone, sends it to OpenAI's API, and copies the transcription to your clipboard.

For Wayland (on Linux), transcribed text will be copied to the clipboard via `wl-copy`.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- `OPENAI_API_KEY` environment variable

## Install

```bash
uv sync
```

## Usage

```bash
uv run simple-transcribe
```

Press **Ctrl+D** to stop recording. The transcription will be copied to your clipboard.

### Options

- `--language` / `--lang` / `-l` — Language code for transcription (e.g. `en`, `ja`)

```bash
uv run simple-transcribe --lang ja
```
