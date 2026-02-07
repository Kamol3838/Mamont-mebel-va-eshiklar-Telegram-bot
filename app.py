import os
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application
from dotenv import load_dotenv

from bot import build_app   # MUHIM

load_dotenv()

TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN:
    raise RuntimeError("TOKEN yo‘q")
if not WEBHOOK_URL:
    raise RuntimeError("WEBHOOK_URL yo‘q")

app = FastAPI()
tg_app: Application | None = None


@app.on_event("startup")
async def on_startup():
    global tg_app
    tg_app = build_app()

    await tg_app.initialize()
    await tg_app.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    await tg_app.start()

    print("✅ WEBHOOK ISHLADI:", f"{WEBHOOK_URL}/webhook")


@app.on_event("shutdown")
async def on_shutdown():
    if tg_app:
        await tg_app.stop()
        await tg_app.shutdown()


@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}


@app.get("/")
def root():
    return {"status": "ok"}
