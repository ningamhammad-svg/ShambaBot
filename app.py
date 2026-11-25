import os
import requests

from flask import Flask, request
from dotenv import load_dotenv

from engine import ask_shambabot

# =====================================
# CONFIGURATION
# =====================================

load_dotenv()

app = Flask(__name__)

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")

PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

PORT = int(os.getenv("PORT", 5000))

GRAPH_VERSION = os.getenv(
    "GRAPH_VERSION",
    "v23.0"
)


# =====================================
# WHATSAPP MESSAGE SENDER
# =====================================

def send_whatsapp_message(phone, message):

    url = (
        f"https://graph.facebook.com/"
        f"{GRAPH_VERSION}/"
        f"{PHONE_NUMBER_ID}/messages"
    )

    headers = {

        "Authorization": f"Bearer {WHATSAPP_TOKEN}",

        "Content-Type": "application/json"

    }

    payload = {

        "messaging_product": "whatsapp",

        "recipient_type": "individual",

        "to": phone,

        "type": "text",

        "text": {

            "preview_url": False,

            "body": message[:4000]

        }

    }

    response = requests.post(

        url,

        headers=headers,

        json=payload,

        timeout=30

    )

    if not response.ok:

        print(
            "WHATSAPP API ERROR:",
            response.status_code,
            response.text
        )

    response.raise_for_status()

    return response.json()


# =====================================
# WEBHOOK VERIFICATION
# =====================================

@app.route("/webhook", methods=["GET"])
def verify_webhook():

    mode = request.args.get("hub.mode")

    token = request.args.get("hub.verify_token")

    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:

        return challenge, 200

    return "Verification failed", 403


# =====================================
# RECEIVE WHATSAPP MESSAGES
# =====================================

@app.route("/webhook", methods=["POST"])
def receive_message():

    data = request.get_json(silent=True) or {}

    try:

        entries = data.get("entry", [])

        for entry in entries:

            changes = entry.get("changes", [])

            for change in changes:

                value = change.get("value", {})

                messages = value.get("messages", [])

                for message in messages:

                    message_type = message.get("type")

                    if message_type != "text":

                        continue

                    phone = message.get("from")

                    text = message.get(
                        "text", {}
                    ).get("body", "").strip()

                    if not phone or not text:

                        continue

                    print(
                        f"NEW FARMER MESSAGE: "
                        f"{phone}: {text}"
                    )

                    # AI PROCESSING

                    answer = ask_shambabot(
                        phone,
                        text
                    )

                    # SEND RESPONSE

                    send_whatsapp_message(
                        phone,
                        answer
                    )

    except Exception as error:

        print(
            "WEBHOOK ERROR:",
            error
        )

    return "EVENT_RECEIVED", 200


# =====================================
# HEALTH CHECK
# =====================================

@app.route("/", methods=["GET"])
def home():

    return {
        "service": "ShambaBot",
        "status": "running",
        "description": "AI Agricultural Assistant"
    }


# =====================================
# START SERVER
# =====================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=PORT,

        debug=False

    )
