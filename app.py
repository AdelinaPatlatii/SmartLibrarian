from dotenv import load_dotenv
from db import load_books_into_chroma
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

        candidates = retrieval_candidates(coll, user_q, k=5)
        answer = make_llm_recommendation(user_q, candidates)
        print(f"Assistant: {answer}\n")


if __name__ == "__main__":
    main()

