"""
Tools for SmartLibrarian.

This file defines helper functions that can be exposed to the LLM via
function calling. The primary tool is get_summary_by_title, which returns
the full summary of a book given its exact title.
"""

from typing import Dict

# Local dictionary of book summaries.
book_summaries_dict: Dict[str, str] = {
    "1984": (
        "O poveste distopică despre o societate totalitară controlată prin supraveghere, "
        "propagandă și poliția gândirii. Winston Smith, protagonistul, se revoltă în secret "
        "împotriva sistemului în căutarea adevărului și a libertății."
    ),
    "The Hobbit": (
        "O poveste plină de aventuri în care hobbitul Bilbo Baggins pornește într-o călătorie "
        "neașteptată. Tema principală este prietenia și curajul descoperit în situații neașteptate."
    ),
    "To Kill a Mockingbird": (
        "Un roman emoționant plasat în Sudul american segregat. Scout Finch își povestește copilăria "
        "în timp ce tatăl ei, Atticus, apără un bărbat de culoare acuzat pe nedrept. "
        "Teme: justiție, moralitate și empatie."
    ),
    "Pride and Prejudice": (
        "Un roman clasic care explorează iubirea, clasa socială și dezvoltarea personală. "
        "Elizabeth Bennet învață să-și depășească prejudecățile, iar domnul Darcy învață "
        "modestia și respectul."
    ),
    "Micul Prinț": (
        "O poveste filosofică despre un mic prinț venit de pe o planetă îndepărtată. "
        "Explorează teme precum inocența copilăriei, iubirea și sensul vieții."
    ),
    "The Great Gatsby": (
        "O poveste tragică despre iubire și ambiție în Epoca Jazzului. Urmărirea lui Jay Gatsby a lui Daisy "
        "reflectă fragilitatea Visului American. Teme: bogăție, iluzie și dorință."
    ),
    "Fahrenheit 451": (
        "Un roman distopic în care cărțile sunt interzise și arse. Pompierul Guy Montag pune sub semnul "
        "întrebării societatea și caută cunoașterea. Teme: cenzură, libertate și revoltă."
    ),
    "Don Quixote": (
        "Considerat primul roman modern, spune povestea unui om care crede că este cavaler și pornește "
        "în aventuri absurde. Teme: idealism, realitate și imaginație."
    ),
    "Jane Eyre": (
        "Drumul unei fete orfane care devine guvernantă. Reziliența și forța morală ale lui Jane "
        "o ajută să treacă prin iubire, greutăți și căutarea independenței."
    ),
    "Frankenstein": (
        "Victor Frankenstein creează o ființă vie din materie moartă, doar pentru a fi îngrozit de rezultat. "
        "Teme: ambiție, responsabilitate și consecințele științei necontrolate."
    ),
}


def get_summary_by_title(title: str) -> str:
    """
    Look up and return the full summary for an exact book title.

    Parameters
    ----------
    title : str
        The exact book title to search for (e.g., "The Hobbit").

    Returns
    -------
    str
        The book's summary if found, otherwise a friendly error message.
    """
    summary = book_summaries_dict.get(title)

    if summary:
        return summary
    else:
        return f"Cartea {title} nu există."


openai_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_summary_by_title",
            "description": "Return the full summary for an exact book title.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Exact book title (e.g., 'The Hobbit')."
                    }
                },
                "required": ["title"],
                "additionalProperties": False
            }
        }
    }
]