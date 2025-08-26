from dotenv import load_dotenv
from db import load_books_into_chroma
from moderation import moderate_or_pass
from rag import retrieval_candidates
from llm import make_llm_recommendation

load_dotenv()


def main():
    coll = load_books_into_chroma()

    while True:
        user_q = input("You: ").strip()
        if not user_q:
            continue
        if user_q.lower() in {"exit", "quit"}:
            break

        warning = moderate_or_pass(user_q)
        if warning:
            print(f"Assistant: {warning}\n")
            continue

        candidates = retrieval_candidates(coll, user_q, k=5)
        answer = make_llm_recommendation(user_q, candidates) # To do: prompt the user for image generation instead of always generating
        print(f"Assistant: {answer}\n")


if __name__ == "__main__":
    main()

