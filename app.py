import os
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# .env faylni o‘qiymiz (local uchun)
load_dotenv()

TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # local: http://127.0.0.1:8000  |  render: https://xxx.onrender.com

app = FastAPI()
tg_app: Application | None = None


# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("Bot ishlayapti ✅")


@app.on_event("startup")
async def startup():
    global tg_app

    if not TOKEN:
        raise RuntimeError("TOKEN yo‘q (.env yoki Render env ga qo‘ying)")

    if not WEBHOOK_URL:
        raise RuntimeError("WEBHOOK_URL yo‘q (.env yoki Render env ga qo‘ying)")

    tg_app = Application.builder().token(TOKEN).build()
    tg_app.add_handler(CommandHandler("start", start))

    await tg_app.initialize()

    # Webhook URL ni tayyorlaymiz
    webhook_full = f"{WEBHOOK_URL.rstrip('/')}/webhook"

    # Telegram webhook faqat HTTPS qabul qiladi
    if webhook_full.startswith("https://"):
        await tg_app.bot.set_webhook(webhook_full)
        print(f"Webhook o‘rnatildi: {webhook_full}")
    else:
        print(f"LOCAL MODE: webhook o‘rnatilmadi (https emas): {webhook_full}")


@app.post("/webhook")
async def webhook(request: Request):
    # Telegram bu endpointga POST qiladi
    data = await request.json()

    if tg_app is None:
        return {"ok": False, "error": "tg_app is not initialized"}

    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}


@app.get("/")
async def root():
    return {"status": "running"}
