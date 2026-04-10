import os
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")
EMERGENCY_TO = os.getenv("EMERGENCY_TO")


def dispatch_alert(incident: dict):
    if not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM, EMERGENCY_TO]):
        print("Twilio is not configured. Alert skipped.")
        return

    client = Client(TWILIO_SID, TWILIO_TOKEN)
    body = (
        f"ACCIDENT detected - severity {incident.get('severity', 'unknown')}"
        f" at {incident.get('timestamp', 'unknown')}"
    )
    if incident.get("location"):
        body += f" | Location: {incident['location']}"

    client.messages.create(
        body=body,
        from_=TWILIO_FROM,
        to=EMERGENCY_TO,
    )
    print("Alert dispatched to emergency contact.")
