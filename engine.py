import os
import json

from pathlib import Path
from google import genai
from dotenv import load_dotenv

from agriculture import AGRICULTURE_SYSTEM


ROOT = Path(__file__).resolve().parents[1]

load_dotenv(ROOT / ".env")

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite"
)

DATABASE = ROOT / "database"

DATABASE.mkdir(
    parents=True,
    exist_ok=True
)

MEMORY_FILE = DATABASE / "memory.json"


def load_memory():

    if not MEMORY_FILE.exists():

        MEMORY_FILE.write_text(
            "{}",
            encoding="utf-8"
        )

    try:

        return json.loads(
            MEMORY_FILE.read_text(
                encoding="utf-8"
            )
        )

    except Exception:

        return {}


def save_memory(memory):

    MEMORY_FILE.write_text(
        json.dumps(
            memory,
            ensure_ascii=False,
            indent=4
        ),
        encoding="utf-8"
    )


def ask_shambabot(phone, message):

    memory = load_memory()

    if phone not in memory:

        memory[phone] = []

    history = memory[phone]

    conversation = ""

    for item in history[-12:]:

        conversation += (
            f"{item['role']}: "
            f"{item['content']}\n"
        )

    prompt = f"""
{AGRICULTURE_SYSTEM}

MAZUNGUMZO YALIYOPITA:

{conversation}

UJUMBE MPYA WA MKULIMA:

{message}

Jibu ujumbe huu kwa kuzingatia mazungumzo
yaliyopita na mahitaji ya mkulima.
"""

    try:

        response = client.models.generate_content(

            model=MODEL,

            contents=prompt

        )

        answer = (response.text or "").strip()

        if not answer:

            return (
                "Samahani, sijapata jibu kwa sasa. "
                "Tafadhali jaribu tena."
            )

        history.append({

            "role": "Mkulima",

            "content": message

        })

        history.append({

            "role": "ShambaBot",

            "content": answer

        })

        # Tunahifadhi mazungumzo ya hivi karibuni.
        memory[phone] = history[-24:]

        save_memory(memory)

        return answer

    except Exception as error:

        print("SHAMBABOT ERROR:", error)

        return (
            "Samahani mkulima, nimepata changamoto "
            "ya kiufundi. Tafadhali jaribu tena "
            "baada ya muda mfupi."
        )


def clear_farmer_memory(phone):

    memory = load_memory()

    if phone in memory:

        del memory[phone]

        save_memory(memory)

        return True

    return False
