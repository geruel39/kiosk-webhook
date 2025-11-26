import os
import stripe
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load Stripe secret key from environment variable
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")  # e.g., sk_test_xxx

# Optional: store payment statuses in memory
PAYMENT_STATUS = {}

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")  # e.g., whsec_xxx

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        print("Webhook verification failed:", e)
        return "Invalid", 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        session_id = session["id"]

        print("Payment completed:", session_id)

        # Update memory
        PAYMENT_STATUS[session_id] = "paid"

        # Forward to Raspberry Pi
        try:
            requests.post(
                "http://192.168.43.106:5005/payment-update",
                json={"session_id": session_id, "status": "paid"},
                timeout=2
            )
            print("Forwarded to Raspberry Pi.")
        except Exception as e:
            print("Could NOT forward to kiosk:", e)

    return "OK", 200

@app.route("/")
def index():
    return jsonify({"status": "Webhook server is running."})

if __name__ == "__main__":
    # Use port 5000 for local testing
    app.run(host="0.0.0.0", port=5000)
