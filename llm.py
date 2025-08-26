"""
LLM integration for SmartLibrarian (simplified).

Responsibilities:
- Ask the LLM for a short recommendation in Romanian.
- Automatically append the full summary of the top candidate book
  using get_summary_by_title().
"""

from typing import List, Dict
from openai import OpenAI
from llm_tools import get_summary_by_title


def _build_messages(user_query: str, candidates: List[Dict[str, str]]) -> list:
    """
    Build chat messages for the LLM.

    We simply give the user request and candidate list,
    and ask for a recommendation in Romanian.
    """
    system_msg = (
        "You are a helpful literary assistant. "
        "Your output MUST be in the same language as the user input in user_query. "
        "You receive the user's request and a list of candidate books. "
        "Choose one and explain briefly (2–4 reasons)."
    )

    context_lines = [f"- {c['title']}: {c['snippet']}" for c in candidates]
    context_block = "Candidați:\n" + "\n".join(context_lines)

    user_msg = (
        f"Cerere: {user_query}\n\n"
        f"{context_block}\n\n"
        "Alege cea mai potrivită carte și explică pe scurt de ce."
    )

    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]


def make_llm_recommendation(user_query: str, candidates: List[Dict[str, str]]) -> str:
    """
    Generate a recommendation in Romanian, then append the full summary
    of the top candidate (assumed to be the best match).
    """
    client = OpenAI()
    messages = _build_messages(user_query, candidates)

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7,
    )
    recommendation = resp.choices[0].message.content or ""

    # Try to detect which candidate title appears in the LLM recommendation
    chosen_title = None
    rec_lower = recommendation.lower()
    for c in candidates:
        title = c["title"]
        if title.lower() in rec_lower:
            chosen_title = title
            break

    # Fallback: if nothing matched, use the top candidate
    if not chosen_title and candidates:
        chosen_title = candidates[0]["title"]

    # Append the correct summary
    if chosen_title:
        summary = get_summary_by_title(chosen_title)
        return f"{recommendation}\n\nRezumat complet pentru „{chosen_title}”:\n{summary}"
    else:
        return recommendation