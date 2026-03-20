import os
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID_PUBLIC = os.environ.get("TELEGRAM_CHAT_ID_PUBLIC")
CHAT_ID_PREMIUM = os.environ.get("TELEGRAM_CHAT_ID_PREMIUM")

async def send_telegram(chat_id: str, message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(url, json=payload)
        return r.text

@app.get("/")
async def root():
    return {"status": "ATM Agent is alive"}

@app.post("/webhook")
async def webhook(request: Request):
    raw = await request.body()
    text = raw.decode("utf-8").replace("\\n", "\n")

    if text:
        await send_telegram(CHAT_ID_PUBLIC, text)
        await send_telegram(CHAT_ID_PREMIUM, text)

    return JSONResponse({"status": "ok"})
