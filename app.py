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
        for entry in data.get("entry", []):

            for change in entry.get("changes", []):

                value = change.get("value", {})

                # =================================
                # CHECK MESSAGE DELIVERY STATUS
                # =================================

                for status in value.get("statuses", []):

                    print(
                        "WHATSAPP DELIVERY STATUS:",
                        status,
                        flush=True
                    )

                    state = status.get("status")
                    message_id = status.get("id")
                    recipient = status.get("recipient_id")

                    if state == "failed":

                        print(
                            "MESSAGE DELIVERY FAILED!",
                            flush=True
                        )

                        print(
                            "ERROR DETAILS:",
                            status.get("errors"),
                            flush=True
                        )

                    elif state == "delivered":

                        print(
                            f"MESSAGE DELIVERED TO {recipient}",
                            flush=True
                        )

                    elif state == "read":

                        print(
                            f"MESSAGE READ BY {recipient}",
                            flush=True
                        )

                # =================================
                # RECEIVE FARMER MESSAGE
                # =================================

                for message in value.get("messages", []):

                    if message.get("type") != "text":
                        continue

                    phone = message.get("from")

                    text = message.get(
                        "text", {}
                    ).get("body", "").strip()

                    if not phone or not text:
                        continue

                    print(
                        f"NEW FARMER MESSAGE: {phone}: {text}",
                        flush=True
                    )

                    print(
                        "STEP 1: GEMINI PROCESSING",
                        flush=True
                    )

                    answer = ask_shambabot(phone, text)

                    print(
                        f"AI RESPONSE: {answer}",
                        flush=True
                    )

                    print(
                        "STEP 2: WHATSAPP SENDING",
                        flush=True
                    )

                    result = send_whatsapp_message(
                        phone,
                        answer
                    )

                    print(
                        "WHATSAPP API RESPONSE:",
                        result,
                        flush=True
                    )

    except Exception:

        import traceback

        traceback.print_exc()

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
