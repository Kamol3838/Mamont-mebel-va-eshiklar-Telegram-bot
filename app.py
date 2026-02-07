# app.py
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from telegram import Update

from bot import build_app  # bot.py ichidagi build_app()

load_dotenv()

TOKEN = os.getenv("TOKEN", "").strip()
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip()  # Render'da bor, lokalda bo'sh

api = FastAPI()
tg_app = None


@api.on_event("startup")
async def on_startup():
    global tg_app
    tg_app = build_app()

    await tg_app.initialize()
    await tg_app.start()

    # Render rejimi: webhook o'rnatamiz
    if WEBHOOK_URL:
        hook = WEBHOOK_URL.rstrip("/") + "/webhook"
        await tg_app.bot.set_webhook(url=hook, drop_pending_updates=True)
        print("✅ WEBHOOK SET:", hook)
    else:
        print("ℹ️ LOCAL MODE: webhook yo'q (polling uchun)")


@api.on_event("shutdown")
async def on_shutdown():
    if tg_app:
        await tg_app.stop()
        await tg_app.shutdown()


@api.get("/")
async def home():
    return {"ok": True, "mode": "webhook" if WEBHOOK_URL else "local"}


@api.post("/webhook")
async def webhook(req: Request):
    data = await req.json()

    # Update ni PTB ga to'g'ri beramiz (callback_query ham shu yerda keladi)
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)

    return {"ok": True}
