import base64
from pathlib import Path
from typing import Optional
from openai import OpenAI


def prompt_from_book(title: str, summary: str, style_hint: Optional[str] = None) -> str:
    """
    Build a concise, descriptive prompt for image generation from a book title & summary.
    """
    base = (
        f"Ilustrație reprezentativă pentru cartea „{title}”. "
        f"Teme și elemente-cheie: {summary} "
        "Imagine clară, expresivă, potrivită ca o copertă modernă. "
        "Fără text pe imagine, focalizare compozițională bună."
    )
    if style_hint:
        base += f" Stil: {style_hint}."
    return base


def generate_image_to_file(
    prompt: str,
    out_path: str = "book_image.png",
    size: str = "1024x1024",
    model: str = "gpt-image-1",
) -> str:
    """
    Generate an image from a text prompt and save it as a PNG.
    """
    out_path = str(Path(out_path).with_suffix(".png"))
    _client = OpenAI()
    result = _client.images.generate(
        model=model,
        prompt=prompt,
        size=size
    )

    image_b64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_b64)
    with open(out_path, "wb") as f:
        f.write(image_bytes)
    return str(Path(out_path).resolve())
