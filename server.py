from __future__ import annotations
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from db import load_books_into_chroma
from rag import retrieval_candidates
from llm import make_llm_recommendation
from moderation import moderate_or_pass
from image_generation import generate_image_to_file, prompt_from_book
from audio_io import tts_save_to_file, transcribe_file
import uvicorn

load_dotenv()

app = FastAPI(title="SmartLibrarian API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:2050",
        "http://127.0.0.1:2050",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# generated media goes into a static/ directory:
STATIC_ROOT = Path("static")
STATIC_ROOT.mkdir(parents=True, exist_ok=True)

# load or create Chroma collection
coll = load_books_into_chroma()


def _safe_name(name: str) -> str:
    return (
        name.strip()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .lower()
    )

@app.post("/api/chat")
def chat(payload: dict):
    user_q = (payload or {}).get("user_q", "").strip()
    if not user_q:
        return JSONResponse({"answer": "Întrebare goală."}, status_code=400)

    warn = moderate_or_pass(user_q)
    if warn:
        return {"answer": warn}

    cands = retrieval_candidates(coll, user_q, k=5)
    answer, title, summary = make_llm_recommendation(user_q, cands)
    return {
        "answer": answer,
        "chosen_title": title,
        "summary": summary,
    }


@app.post("/api/image")
def image(payload: dict):
    title = (payload or {}).get("title") or ""
    summary = (payload or {}).get("summary") or ""
    if not title or not summary:
        return JSONResponse({"error": "title & summary are required"}, status_code=400)

    safe_title = _safe_name(title)
    out_path = STATIC_ROOT / f"{safe_title}.png"

    prompt = prompt_from_book(title, summary)
    generate_image_to_file(prompt=prompt, out_path=str(out_path), size="1024x1024", model="gpt-image-1")
    return {"image_url": f"/{out_path.name}"}


@app.post("/api/tts")
def tts(payload: dict):
    text = (payload or {}).get("text", "").strip()
    book_title = (payload or {}).get("book_title")
    if not text:
        return JSONResponse({"error": "text is required"}, status_code=400)

    if book_title:
        base = Path(_safe_name(book_title)).stem
        final_name = f"{base}.mp3"
    else:
        final_name = "default.mp3"

    target = STATIC_ROOT / final_name
    tmp_path_str = tts_save_to_file(text=text, book_title=final_name)
    tmp_path = Path(tmp_path_str)
    if tmp_path.resolve() != target.resolve():
        target.write_bytes(tmp_path.read_bytes())

    return {"audio_url": f"/{target.name}"}


@app.post("/api/stt")
def stt(file: UploadFile = File(...), language: Optional[str] = Form(None)):
    import tempfile, shutil

    suffix = Path(file.filename or "").suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        text = transcribe_file(tmp_path, language=language)
        return {"text": text}
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


app.mount("/", StaticFiles(directory=str(STATIC_ROOT), html=True), name="root")

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=2050, reload=True)
