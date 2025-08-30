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
    book_title: str,
    voice: str = "alloy",
    audio_format: str = "mp3",
    model: str = "gpt-4o-mini-tts",
) -> str:
    """
    Convert text to speech and save to an audio file using streaming.
    """
    client = OpenAI()
    safe_name = book_title.replace(" ", "_").replace("/", "_").lower()
    out = Path(f"{safe_name}_recommendation.{audio_format}")

    with client.audio.speech.with_streaming_response.create(
        model=model,
        voice=voice,
        input=text,
        response_format=audio_format,
    ) as response:
        response.stream_to_file(str(out))

    return str(out.resolve())

