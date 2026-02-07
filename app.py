import os
from fastapi import FastAPI, Request
from telegram import Update

from bot import build_app

app = FastAPI()
tg_app = build_app()


@app.on_event("startup")
async def on_startup():
    await tg_app.initialize()
    await tg_app.start()

    webhook_url = os.getenv("WEBHOOK_URL", "").strip()

    # Render: HTTPS bo'lsa webhook qo'yamiz
    if webhook_url.startswith("https://"):
        await tg_app.bot.set_webhook(url=webhook_url)
        print("✅ WEBHOOK set:", webhook_url)
    else:
        # Lokal: webhook qo'ymaymiz (Telegram HTTPS talab qiladi)
        print("ℹ️ LOCAL MODE: webhook o‘rnatilmadi (WEBHOOK_URL https emas yoki yo‘q)")


@app.on_event("shutdown")
async def on_shutdown():
    await tg_app.stop()
    await tg_app.shutdown()


@app.get("/")
async def root():
    return {"ok": True}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}
