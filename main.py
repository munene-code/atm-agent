import os
import json
import logging
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID_PUBLIC = os.environ.get("TELEGRAM_CHAT_ID_PUBLIC")
CHAT_ID_PREMIUM = os.environ.get("TELEGRAM_CHAT_ID_PREMIUM")


async def send_telegram(chat_id: str, message: str) -> str:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    logger.info("Sending Telegram message to chat_id=%s", chat_id)
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(url, json=payload)
        logger.info("Telegram API response [chat_id=%s]: %s", chat_id, r.text)
        return r.text


@app.get("/")
async def root():
    return {"status": "ATM Agent is alive"}


@app.post("/webhook")
async def webhook(request: Request):
    raw = await request.body()
    body = raw.decode("utf-8")
    logger.info("Webhook received body: %s", body)

    # Try to parse as JSON first (direct JSON posts with chat_id + text fields).
    # Fall back to treating the entire body as a plain-text TradingView alert.
    try:
        data = json.loads(body)
        chat_id = str(data.get("chat_id", "")).strip()
        message = data.get("text", "").replace("\\n", "\n").strip()
        logger.info("Parsed as JSON — chat_id=%s", chat_id)

        if not chat_id or not message:
            logger.warning("JSON payload missing chat_id or text")
            return JSONResponse(
                {"status": "error", "detail": "JSON payload missing chat_id or text"},
                status_code=400,
            )

        try:
            result = await send_telegram(chat_id, message)
            return JSONResponse({"status": "ok", "telegram_response": result})
        except Exception as exc:
            logger.exception("Failed to send Telegram message: %s", exc)
            return JSONResponse(
                {"status": "error", "detail": str(exc)},
                status_code=500,
            )

    except json.JSONDecodeError:
        # Plain-text body — TradingView alert format.
        message = body.replace("\\n", "\n").strip()
        logger.info("Parsed as plain text (TradingView alert)")

        if not message:
            logger.warning("Plain-text body is empty")
            return JSONResponse(
                {"status": "error", "detail": "Empty message body"},
                status_code=400,
            )

        chat_ids = [cid for cid in [CHAT_ID_PUBLIC, CHAT_ID_PREMIUM] if cid]
        if not chat_ids:
            logger.error(
                "No Telegram chat IDs configured "
                "(TELEGRAM_CHAT_ID_PUBLIC / TELEGRAM_CHAT_ID_PREMIUM)"
            )
            return JSONResponse(
                {"status": "error", "detail": "No chat IDs configured"},
                status_code=500,
            )

        results = {}
        errors = {}
        for chat_id in chat_ids:
            try:
                result = await send_telegram(chat_id, message)
                results[chat_id] = result
            except Exception as exc:
                logger.exception(
                    "Failed to send Telegram message to chat_id=%s: %s", chat_id, exc
                )
                errors[chat_id] = str(exc)

        if errors and not results:
            return JSONResponse(
                {"status": "error", "errors": errors},
                status_code=500,
            )

        return JSONResponse(
            {"status": "ok", "telegram_responses": results, "errors": errors}
        )
