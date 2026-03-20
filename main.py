import os
import json
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

async def send_telegram(chat_id: str, message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(url, json=payload)
        return r.text

@app.get("/")
async def root():
    return {"status": "ATM Agent is alive"}

@app.post("/webhook")
async def webhook(request: Request):
    raw = await request.body()
    text = raw.decode("utf-8")
    text = text.replace("\\n", "\n")
    try:
        data = json.loads(text)
        chat_id = str(data.get("chat_id", ""))
        message = data.get("text", "")
        message = message.replace("\\n", "\n")
        if chat_id and message:
            await send_telegram(chat_id, message)
    except:
        pass
    return JSONResponse({"status": "ok"})
