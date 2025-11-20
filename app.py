from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/")
async def index():
    return {"message": "Webhook server is running!"}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print("Webhook received:", data)
    return {"status": "ok"}
