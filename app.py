from dotenv import load_dotenv
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

        warning = moderate_or_pass(user_q)
        if warning:
            print(f"Assistant: {warning}\n")
            continue

        candidates = retrieval_candidates(coll, user_q, k=5)
        recommendation, chosen_title, summary = make_llm_recommendation(user_q, candidates)
        answer = recommendation
        if chosen_title and summary:
            answer += f"\n\nRezumat complet pentru {chosen_title}:\n{summary}"

        print(f"Assistant: {answer}\n")

        if chosen_title:
            choice = input("Generate an image for this recommendation? [y/n]: ").strip().lower()
            if choice == "y":
                safe_name = chosen_title.replace(" ", "_").replace("/", "_").lower() # remove annoying characters from file name
                print(f"Generating image {safe_name}.png...\n")
                spawn_image_job(chosen_title, summary, safe_name)
            elif choice == "n":
                continue


if __name__ == "__main__":
    main()

