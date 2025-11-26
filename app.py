from flask import Flask, request
import os
import requests
import stripe

app = Flask(__name__)

# Load secrets from environment variables
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

# Store payment status in memory (optional)
PAYMENT_STATUS = {}

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        print("Webhook verification failed:", e)
        return "Invalid", 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        session_id = session["id"]

        print("Payment completed:", session_id)
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

if __name__ == "__main__":
    # Use port 10000 to match your previous attempts
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
