from typing import List, Dict, Any


def _make_snippet(text: str, max_len: int = 220) -> str:
    """
    Build a compact one-line snippet from a longer document string.
    """
    if not text:
        return ""
    one_line = text.replace("\n", " ").strip()
    return one_line if len(one_line) <= max_len else one_line[:max_len].rstrip() + "..."


def retrieval_candidates(
    coll,
    query_text: str,
    k: int = 5,
    snippet_len: int = 220,
) -> List[Dict[str, Any]]:
    """
    Run a semantic query against a Chroma collection and return top-K candidates.

    This function expects the collection to have an embedding function attached
    (e.g., OpenAI embeddings) so that `query_texts` triggers vector search.

    Parameters
    ----------
    coll :
        A Chroma collection instance (e.g., returned by `get_or_create_collection`).
    query_text : str
        The user query in Romanian (free-form). Example: "Vreau o carte despre prietenie și magie".
    k : int
        Number of results to return (top-K).
    snippet_len : int
        Maximum length of the text snippet for each candidate.

    Returns
    -------
    List[Dict[str, Any]]
        A list of candidate dictionaries with a stable schema:
        [
          {
            "title": str,      # book title (from metadatas["title"] or from id)
            "snippet": str,    # short preview from the stored document
            "distance": float, # vector distance (smaller = closer match)
            "id": str          # the raw Chroma ID
          },
          ...
        ]
    """
    res = coll.query(
        query_texts=[query_text],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    ids = (res.get("ids") or [[]])[0]
    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]

    out: List[Dict[str, Any]] = []
    for i in range(len(ids)):
        doc_id = ids[i]
        doc_text = docs[i] if i < len(docs) else ""
        meta = metas[i] if i < len(metas) and isinstance(metas[i], dict) else {}
        dist = dists[i] if i < len(dists) else None

        title = meta.get("title") or doc_id
        snippet = _make_snippet(doc_text, max_len=snippet_len)

        out.append(
            {
                "title": title,
                "snippet": snippet,
                "distance": dist,
                "id": doc_id,
            }
        )

    return out
