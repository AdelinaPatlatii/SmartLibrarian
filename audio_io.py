from pathlib import Path
from typing import Optional
from openai import OpenAI

def transcribe_file(audio_path: str, model: str = "whisper-1", language: Optional[str] = None) -> str:
    """
    Transcribe a local audio file to text using OpenAI Whisper.
    """
    p = Path(audio_path)
    if not p.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    _client = OpenAI()
    with p.open("rb") as f:
        resp = _client.audio.transcriptions.create(
            model=model,
            file=f,
            language=language,
        )
    return resp.text or ""


def tts_save_to_file(
    text: str,
    out_path: str = "answer.mp3",
    voice: str = "alloy",
    audio_format: str = "mp3",
    model: str = "gpt-4o-mini-tts",
) -> str:
    """
    Convert text to speech and save to an audio file.
    """
    out = Path(out_path).with_suffix(f".{audio_format}")

    _client = OpenAI()
    resp = _client.audio.speech.create(
        model=model,
        voice=voice,
        input=text,
        format=audio_format,
    )

    with out.open("wb") as f:
        f.write(resp.read())
    return str(out.resolve())
