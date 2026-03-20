import os
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_PREMIUM = os.environ.get("TELEGRAM_CHAT_ID_PREMIUM")
CHAT_PUBLIC = os.environ.get("TELEGRAM_CHAT_ID_PUBLIC")

async def send_telegram(chat_id: str, message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload)

@app.get("/")
async def root():
    return {"status": "ATM Agent is alive"}

@app.post("/webhook")
async def webhook(request: Request):
    body = await request.body()
    message = body.decode("utf-8")
    if CHAT_PREMIUM:
        await send_telegram(CHAT_PREMIUM, message)
    if CHAT_PUBLIC:
        await send_telegram(CHAT_PUBLIC, message)
    return JSONResponse({"status": "sent"})
