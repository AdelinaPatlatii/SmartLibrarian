from enum import Enum
from typing import Optional
from pydantic import BaseModel
from openai import OpenAI

class Category(str, Enum):
    violence = "violence"
    sexual = "sexual"
    self_harm = "self_harm"
    offensive = "offensive"


class ContentCompliance(BaseModel):
    is_violating: bool
    category: Optional[Category]
    explanation_if_violating: Optional[str]


def check_message_compliance(message: str) -> ContentCompliance:
    """
    Ask the model to classify the user message.
    """
    client = OpenAI()
    response = client.responses.parse(
        model="gpt-4o-2024-08-06",
        input=[
            {
                "role": "system",
                "content": (
                    "Determine if the user input violates any of these categories: "
                    "violence, sexual, self_harm, offensive. "
                    "The 'offensive' category includes profanity, slurs, hate/harassment, "
                    "demeaning insults, or otherwise abusive/derogatory language. "
                    "If violating, set is_violating=true, provide the best-fitting category "
                    "and a brief explanation. If not, set is_violating=false."
                ),
            },
            {"role": "user", "content": message},
        ],
        text_format=ContentCompliance,
    )
    return response.output_parsed


def moderate_or_pass(message: str) -> Optional[str]:
    """
    Apply moderation. If violation is detected, return a respectful warning.
    """
    compliance = check_message_compliance(message)

    if compliance.is_violating:
        return (
            "Te rog să folosești un limbaj respectuos. "
            "Mesajul tău pare să conțină conținut nepotrivit."
        )
    return None
