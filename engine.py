import os
import json
import logging

from pathlib import Path
from google import genai
from dotenv import load_dotenv

from agriculture import AGRICULTURE_SYSTEM


# =====================================
# CONFIGURATION
# =====================================

ROOT = Path(__file__).resolve().parent

load_dotenv(ROOT / ".env")

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("ShambaBot")

API_KEY = os.getenv("GEMINI_API_KEY")

MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.1-flash-lite"
)

if not API_KEY:
    logger.error("GEMINI_API_KEY haijapatikana!")

client = genai.Client(
    api_key=API_KEY
) if API_KEY else None


# =====================================
# MEMORY DATABASE
# =====================================

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

    except Exception as error:

        logger.error(
            "Memory loading error: %s",
            error
        )

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


# =====================================
# SHAMBABOT AI ENGINE
# =====================================

def ask_shambabot(phone, message):

    logger.info(
        "Processing farmer message: %s",
        phone
    )

    if not client:

        logger.error(
            "Gemini client haijaanzishwa. "
            "Kagua GEMINI_API_KEY."
        )

        return (
            "Samahani mkulima, huduma yetu ya AI "
            "haipatikani kwa sasa. Tafadhali jaribu tena."
        )

    try:

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

MAELEKEZO YA ZIADA:

- Wewe ni ShambaBot, mtaalamu wa masuala ya kilimo.
- Jibu kwa lugha ambayo mkulima ametumia.
- Tumia Kiswahili fasaha pale mkulima anapotumia Kiswahili.
- Toa majibu yenye manufaa na yanayotekelezeka.
- Uliza maswali ya ziada pale taarifa hazijakamilika.
- Usibuni taarifa za kisayansi au dawa za mimea.
- Toa tahadhari kuhusu matumizi salama ya viuatilifu.
- Usijibu nje ya mada bila sababu.

MAZUNGUMZO YALIYOPITA:

{conversation}

UJUMBE MPYA WA MKULIMA:

{message}

Jibu ujumbe huu kwa kuzingatia historia ya mazungumzo.
"""

        logger.info(
            "Sending request to Gemini model: %s",
            MODEL
        )

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

        answer = (response.text or "").strip()

        if not answer:

            logger.warning(
                "Gemini returned empty response."
            )

            return (
                "Samahani mkulima, sijapata jibu kwa sasa. "
                "Tafadhali jaribu tena."
            )

        # SAVE FARMER MESSAGE

        history.append({

            "role": "Mkulima",

            "content": message

        })

        # SAVE AI RESPONSE

        history.append({

            "role": "ShambaBot",

            "content": answer

        })

        # KEEP RECENT CONVERSATION

        memory[phone] = history[-24:]

        save_memory(memory)

        logger.info(
            "Gemini response generated successfully."
        )

        return answer

    except Exception:

        logger.exception(
            "SHAMBABOT GEMINI ERROR"
        )

        return (
            "Samahani mkulima, nimepata changamoto "
            "ya kiufundi wakati wa kutengeneza jibu. "
            "Tafadhali jaribu tena baada ya muda mfupi."
        )


# =====================================
# CLEAR FARMER MEMORY
# =====================================

def clear_farmer_memory(phone):

    memory = load_memory()

    if phone in memory:

        del memory[phone]

        save_memory(memory)

        logger.info(
            "Memory cleared for farmer: %s",
            phone
        )

        return True

    return False
