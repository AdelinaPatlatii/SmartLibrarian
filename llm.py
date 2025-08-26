from typing import List, Dict
from openai import OpenAI
from image_generation import prompt_from_book, generate_image_to_file
from llm_tools import get_summary_by_title
import threading

_IMG_SIZE = "1024x1024"

def _build_messages(user_query: str, candidates: List[Dict[str, str]]) -> list:
    """
    Build chat messages for the LLM.

    We give the user request and candidate list,
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


def _spawn_image_job(title: str, summary: str) -> None:
    """Fire-and-forget image generation to avoid blocking the text output."""
    def _job():
        try:
            img_prompt = prompt_from_book(title, summary)
            safe_name = title.replace(" ", "_").replace("/", "_").lower()
            # Pass a smaller/fixed size to speed things up
            generate_image_to_file(img_prompt, out_path=f"{safe_name}.png", size=_IMG_SIZE)
        except Exception:
            # Keep silent in CLI to avoid noise; optionally log here.
            pass

    t = threading.Thread(target=_job, daemon=True)
    t.start()


def make_llm_recommendation(user_query: str, candidates: List[Dict[str, str]]) -> str:
    """
    Generate a recommendation in Romanian, then append the full summary
    """
    client = OpenAI()
    messages = _build_messages(user_query, candidates)

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7,
    )
    recommendation = resp.choices[0].message.content or ""

    # try to detect which candidate title appears in the LLM recommendation
    chosen_title = None
    rec_lower = recommendation.lower()
    for c in candidates:
        title = c["title"]
        if title.lower() in rec_lower:
            chosen_title = title
            break

    # if nothing matched, use the top candidate
    if not chosen_title and candidates:
        chosen_title = candidates[0]["title"]

    if chosen_title:
        summary = get_summary_by_title(chosen_title)

        # kick off image generation WITHOUT blocking the text response
        _spawn_image_job(chosen_title, summary)

        # final text response
        return (
            f"{recommendation}\n\n"
            f"Rezumat complet pentru „{chosen_title}”:\n{summary}\n\n"
            f"(Imaginea se generează în fundal.)"
        )
    else:
        return recommendation