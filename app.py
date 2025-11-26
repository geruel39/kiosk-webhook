from flask import Flask, request, jsonify
import stripe
import os
import base64
import qrcode
from io import BytesIO

app = Flask(__name__)

# Stripe config
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

# In-memory storage
PAYMENT_STATUS = {}  # session_id -> "pending"/"paid"

@app.route("/")
def index():
    return "Webhook server is running!"

@app.route("/create_payment")
def create_payment():
    # Get amount from query params
    amount = request.args.get("amount")
    if not amount:
        return jsonify({"error": "Amount required"}), 400

    # Create a Stripe checkout session
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "php",
                    "product_data": {"name": "Kiosk Payment"},
                    "unit_amount": int(float(amount) * 100),  # in cents
                },
                "quantity": 1
            }],
            mode="payment",
            success_url="https://your-success-url.com",
            cancel_url="https://your-cancel-url.com"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Generate QR code for payment URL
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(session.url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_b64 = base64.b64encode(buffer.getvalue()).decode()

    # Store as pending
    PAYMENT_STATUS[session.id] = "pending"

    return jsonify({"session_id": session.id, "qr_image": qr_b64})

@app.route("/check_payment")
def check_payment():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id required"}), 400

    status = PAYMENT_STATUS.get(session_id, "pending")
    return jsonify({"status": status})

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")
    endpoint_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        print("Webhook verification failed:", e)
        return "Invalid", 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        session_id = session["id"]
        PAYMENT_STATUS[session_id] = "paid"
        print("Payment completed:", session_id)

    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
