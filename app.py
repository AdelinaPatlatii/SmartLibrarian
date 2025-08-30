from dotenv import load_dotenv
from audio_io import tts_save_to_file, transcribe_file
from db import load_books_into_chroma
from moderation import moderate_or_pass
from rag import retrieval_candidates
from llm import make_llm_recommendation
from image_generation import spawn_image_job

load_dotenv()


def main():
    coll = load_books_into_chroma()

    while True:
        user_q = input("Your input: ").strip()
        if not user_q:
            continue
        if user_q.lower() in {"exit", "quit"}:
            break

        # speech-to-text transcription part
        if user_q == ":stt":
            path = input("Audio file path to transcribe: ").strip()
            if not path:
                print("Assistant: No file provided.\n")
                continue
            try:
                user_q = transcribe_file(path, language="ro")
                print(f"[Transcribed] {user_q}\n")
            except Exception as e:
                print(f"Assistant: Could not transcribe audio ({e}).\n")
                continue

        # prompt moderation part
        warning = moderate_or_pass(user_q)
        if warning:
            print(f"Assistant: {warning}\n")
            continue

        candidates = retrieval_candidates(coll, user_q, k=5)
        recommendation, chosen_title, summary = make_llm_recommendation(user_q, candidates)

        # text answer generation part
        answer = recommendation
        if chosen_title and summary:
            answer += f"\n\nRezumat complet pentru {chosen_title}:\n{summary}"

        print(f"Assistant: {answer}\n")

        # text-to-speech part
        choice_tts = input("Generate audio for this answer? [y/n]: ").strip().lower()
        if choice_tts == "y":
            try:
                book_title = chosen_title or "default.mp3"
                out_path = tts_save_to_file(answer, book_title)
                print(f"Assistant: Audio saved to {out_path}\n")
            except Exception as e:
                print(f"Assistant: Could not synthesize audio ({e}).\n")

        # image generation part
        if chosen_title:
            choice_image_gen = input("Generate an image for this recommendation? [y/n]: ").strip().lower()
            if choice_image_gen == "y":
                safe_name = chosen_title.replace(" ", "_").replace("/", "_").lower() # remove annoying characters from file name
                print(f"Generating image {safe_name}.png...\n")
                spawn_image_job(chosen_title, summary, safe_name)


if __name__ == "__main__":
    main()

