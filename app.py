from flask import Flask, request, jsonify
import stripe
import requests
import os

app = Flask(__name__)

# Use environment variable for your Stripe secret key
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")  # Set this in Render dashboard

# Optional in-memory payment status storage
PAYMENT_STATUS = {}

@app.route("/")
def index():
    return "Webhook server is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")
    endpoint_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")  # Set in Render dashboard

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

        try:
            requests.post(
                "http://192.168.43.106:5005/payment-update",
                json={"session_id": session_id, "status": "paid"},
                timeout=2
            )
            print("Forwarded to Raspberry Pi.")
        except Exception as e:
            print("Could NOT forward to kiosk:", e)

    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
