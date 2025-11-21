from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()  # load .env variables

app = FastAPI()

WEBHOOK_SECRET = os.getenv("PAYMONGO_WEBHOOK_SECRET")

@app.get("/")
async def index():
    return {"message": "Webhook server is running!"}

@app.post("/webhook")
async def webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("Paymongo-Signature")  # header from PayMongo

    # Verify signature
    if not verify_signature(payload, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    data = await request.json()
    print("Webhook received:", data)
    return {"status": "ok"}


def verify_signature(payload: bytes, signature: str) -> bool:
    if not signature:
        return False
    computed_hmac = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(computed_hmac, signature)
