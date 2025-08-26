import chromadb
from chromadb.utils import embedding_functions
import os

def parse_books(txt_path):
    titles, summaries = [], []
    current_title, current_summary_lines = None, []

    with open(txt_path, "r", encoding="utf-8") as f:
        for line in (l.rstrip("\n") for l in f):
            if line.startswith("## Title:"):
                if current_title is not None:
                    titles.append(current_title)
                    summaries.append("\n".join(current_summary_lines).strip())
                    current_summary_lines = []
                current_title = line[len("## Title:"):].strip()
            else:
                current_summary_lines.append(line)

    if current_title is not None:
        titles.append(current_title)
        summaries.append("\n".join(current_summary_lines).strip())

    return titles, summaries


def load_books_into_chroma(txt_path="books_summaries.txt", db_path="./chroma_db", collection_name="books"):
    titles, docs = parse_books(txt_path)

    ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.environ["OPENAI_API_KEY"],
        model_name="text-embedding-3-small"
    )

    client = chromadb.PersistentClient(path=db_path)
    coll = client.get_or_create_collection(collection_name, embedding_function=ef)

    # Titles act as IDs
    if coll.count() == 0:
        coll.add(documents=docs, ids=titles)

    return coll


if __name__ == "__main__":
    collection = load_books_into_chroma()
    print(f"Loaded {collection.count()} books into ChromaDB.")
