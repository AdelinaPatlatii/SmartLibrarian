"""
LLM integration for SmartLibrarian.

Responsibilities:
- Build a prompt in Romanian (user-facing) while keeping code and comments in English.
- Send retrieval candidates (RAG results) to the LLM as context.
- Allow the model to optionally call a local tool: get_summary_by_title(title: str).
- Return a concise conversational recommendation in Romanian.

Requirements:
- OPENAI_API_KEY must be available in the environment (loaded by the app entrypoint).
- `llm_tools.py` must define:
    - `openai_tools`: the OpenAI function-calling schema for get_summary_by_title
    - `get_summary_by_title(title: str) -> str`: local function to return a full summary
"""

from typing import List, Dict
import json
from openai import OpenAI
from llm_tools import get_summary_by_title, openai_tools


def _build_messages(user_query: str, candidates: List[Dict[str, str]]) -> list:
    """
    Construct chat messages for the LLM.

    Notes:
    - System prompt is in English (clear, explicit instructions).
    - User-facing content (the "user" message) is in Romanian, per product requirement.
    """
    system_msg = (
        "You are a helpful literary assistant. "
        "Your output MUST be in Romanian. "
        "You receive the user's request and a list of candidate books from a vector search. "
        "Choose the single best recommendation and justify it briefly (2–4 reasons). "
        "Be concise, friendly, and name the exact book title. "
        "If the user asks for a full summary of an exact title, use the provided tool."
    )

    # Romanian user message with RAG context
    # Each candidate is a dictionary like: {"title": str, "snippet": str, "distance": float}
    context_lines = [f"- {c['title']}: {c['snippet']}" for c in candidates]
    context_block = "Candidați (din căutare semantică):\n" + "\n".join(context_lines)

    user_msg = (
        f"Cerere: {user_query}\n\n"
        f"{context_block}\n\n"
        "Alege cea mai potrivită carte și explică pe scurt de ce."
    )

    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]


def _handle_tool_call_once(client: OpenAI, messages: list, tool_call) -> str:
    """
    Execute a single tool call requested by the model and return the final assistant text.

    This handles one round-trip:
      - Execute the requested function (currently: get_summary_by_title).
      - Append the tool result to the conversation.
      - Ask the model for a final answer (no further tool calls).
    """
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments or "{}")

    if name == "get_summary_by_title":
        title = args.get("title", "")
        summary = get_summary_by_title(title)
        # Add the tool result to the conversation
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": "get_summary_by_title",
                "content": summary,
            }
        )
        # Ask the model for a final message after the tool output
        followup = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
        )
        return followup.choices[0].message.content or ""

    # Unknown tool name (should not happen with the provided schema)
    return "Nu am putut apela uneltele necesare pentru acest răspuns."


def make_llm_recommendation(user_query: str, candidates: List[Dict[str, str]]) -> str:
    """
    Generate a conversational recommendation in Romanian using OpenAI Chat Completions.

    Parameters
    ----------
    user_query : str
        The user's Romanian request, e.g., "Vreau o carte despre prietenie și magie".
    candidates : List[Dict[str, str]]
        Top-K RAG results. Each dict should include:
          - "title": str (book title)
          - "snippet": str (short text excerpt or summary)
          - "distance": float (optional; used for debugging/ordering)

    Returns
    -------
    str
        A concise recommendation in Romanian. If the model requests a tool call
        (get_summary_by_title), the function executes it and returns the final answer.
    """
    client = OpenAI()
    messages = _build_messages(user_query, candidates)

    # First LLM call with tool schema enabled
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=openai_tools,
        tool_choice="auto",
        temperature=0.7,
    )

    choice = resp.choices[0]
    print(choice)
    # If the model chooses to call a tool (e.g., full summary by title)
    if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
        # Add the assistant message that contains the tool call request
        messages.append(choice.message)
        # Execute only the first tool call (sufficient for this app)
        return _handle_tool_call_once(client, messages, choice.message.tool_calls[0])

    # Otherwise, return the assistant text directly
    return choice.message.content or "Nu am un răspuns momentan."
