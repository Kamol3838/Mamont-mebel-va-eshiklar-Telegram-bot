import os
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application

# =====================
# ENV
# =====================
load_dotenv()

TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN:
    raise RuntimeError("❌ TOKEN yo‘q (.env yoki Render env ga qo‘ying)")
if not WEBHOOK_URL:
    raise RuntimeError("❌ WEBHOOK_URL yo‘q (.env yoki Render env ga qo‘ying)")

# =====================
# FASTAPI
# =====================
app = FastAPI()
tg_app: Application | None = None


# =====================
# STARTUP
# =====================
@app.on_event("startup")
async def on_startup():
    global tg_app

    tg_app = Application.builder().token(TOKEN).build()
    await tg_app.initialize()

    webhook_full = WEBHOOK_URL.rstrip("/") + "/webhook"

    # Telegram faqat HTTPS webhook qabul qiladi
    if webhook_full.startswith("https://"):
        await tg_app.bot.set_webhook(webhook_full)
        print(f"✅ Webhook o‘rnatildi: {webhook_full}")
    else:
        print(f"ℹ️ LOCAL MODE: webhook o‘rnatilmadi (https emas): {webhook_full}")


# =====================
# TELEGRAM WEBHOOK
# =====================
@app.post("/webhook")
async def telegram_webhook(request: Request):
    if tg_app is None:
        return {"ok": False, "error": "Bot hali init bo‘lmagan"}

    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}


# =====================
# ROOT (Health check)
# =====================
@app.get("/")
async def root():
    return {"status": "running"}
