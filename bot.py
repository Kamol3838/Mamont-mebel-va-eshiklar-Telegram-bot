from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import List

from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
    InputFile,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================== ENV ==================
load_dotenv()

TOKEN = os.getenv("TOKEN", "").strip()
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip()

ADMIN_CHAT_IDS_RAW = os.getenv("ADMIN_CHAT_IDS", "").strip()  # masalan: "1469..., -1003..."
# Eski .env larda "ADMIN_ID" deb yozilgan bo‘lishi mumkin — fallback:
if not ADMIN_CHAT_IDS_RAW:
    ADMIN_CHAT_IDS_RAW = os.getenv("ADMIN_ID", "").strip()


def parse_chat_ids(raw: str) -> List[int]:
    ids: List[int] = []
    for part in (raw or "").replace("\n", " ").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.append(int(part))
        except ValueError:
            pass
    return ids


ADMIN_CHAT_IDS: List[int] = parse_chat_ids(ADMIN_CHAT_IDS_RAW)

BRAND_TITLE = "🏠 Mamont mebel va eshiklar"

PHONES = ["+998946103838", "+998906144440"]
TG_USERNAME = "@bazizbuxara"
IG_USERNAME = "@jumayev1992"

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"

PORTFOLIO = {
    "oshxona": ["oshxona1.jpg", "oshxona2.jpg", "oshxona3.jpg"],
    "holl": ["holl1.jpg", "holl2.jpg", "holl3.jpg"],
    "bolalar": ["bolalar1.jpg", "bolalar2.jpg", "bolalar3.jpg"],
    "shkaf": ["shkaf1.jpg", "shkaf2.jpg", "shkaf3.jpg"],
    "ofis": ["ofis1.jpg", "ofis2.jpg", "ofis3.jpg"],
}


# ================== YORDAMCHI ==================
def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🪑 Mebel xizmati", callback_data="svc:mebel")],
            [InlineKeyboardButton("🚪 Eshiklar xizmati", callback_data="svc:eshik")],
            [InlineKeyboardButton("🎨 Bo‘yash xizmati", callback_data="svc:boyash")],
            [InlineKeyboardButton("💻 Konstruktlash xizmati", callback_data="svc:konstruktor")],
            [InlineKeyboardButton("🧑‍🔧 Ustalar xizmati", callback_data="svc:ustalar")],
            [
                InlineKeyboardButton("📞 Aloqa", callback_data="contact"),
                InlineKeyboardButton("⭐ Fikrlar", callback_data="reviews"),
            ],
        ]
    )


def mebel_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🍽 Oshxona", callback_data="mebel:oshxona")],
            [InlineKeyboardButton("🪑 Holl", callback_data="mebel:holl")],
            [InlineKeyboardButton("🧸 Bolalar yotoqxonasi", callback_data="mebel:bolalar")],
            [InlineKeyboardButton("🚪 Shkaf-kupe", callback_data="mebel:shkaf")],
            [InlineKeyboardButton("🏢 Ofis mebellari", callback_data="mebel:ofis")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="back:main")],
        ]
    )


def section_actions_kb(section_key: str, back_to: str) -> InlineKeyboardMarkup:
    # section_key: "mebel/oshxona" yoki "svc/eshik"
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🧾 Narx so‘rash", callback_data=f"ask:{section_key}"),
                InlineKeyboardButton("🖼 Ish namunalari", callback_data=f"pf:{section_key}"),
            ],
            [
                InlineKeyboardButton("📞 Aloqa", callback_data="contact"),
                InlineKeyboardButton("⭐ Fikrlar", callback_data="reviews"),
            ],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data=back_to)],
        ]
    )


async def send_to_admins(app: Application, text: str) -> None:
    if not ADMIN_CHAT_IDS:
        return
    for chat_id in ADMIN_CHAT_IDS:
        try:
            await app.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            pass


async def send_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str) -> None:
    files = PORTFOLIO.get(key, [])
    sent_any = False

    for fn in files:
        path = IMAGES_DIR / fn
        if path.exists() and path.is_file():
            sent_any = True
            await update.effective_chat.send_photo(photo=InputFile(path))

    if not sent_any:
        await update.effective_chat.send_message(
            "⚠️ Hozircha bu bo‘limga rasmlar qo‘shilmagan.\n"
            "✅ images/ papkaga rasmlarni qo‘ying va PORTFOLIO ro‘yxatini moslang.",
            parse_mode=ParseMode.MARKDOWN,
        )


# ================== HANDLERS ==================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /start bosilganda menyu chiqadi
    await update.message.reply_text(
        f"{BRAND_TITLE}\n\nXizmat turini tanlang 👇",
        reply_markup=main_menu_kb(),
        parse_mode=ParseMode.MARKDOWN,
    )


async def on_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Telegram contact yuborganda adminlarga jo‘natish
    if not update.message or not update.message.contact:
        return

    c = update.message.contact
    user = update.effective_user

    msg = (
        "📞 *Mijoz telefon ulashdi*\n\n"
        f"👤 *Mijoz:* {user.full_name}\n"
        f"🆔 *User ID:* {user.id}\n"
        f"📱 *Telefon:* {c.phone_number}\n"
        f"🕒 *Vaqt:* {now_str()}"
    )

    await send_to_admins(context.application, msg)

    await update.message.reply_text("✅ Rahmat! Telefon raqamingiz qabul qilindi.", reply_markup=ReplyKeyboardRemove())


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    waiting = context.user_data.get("waiting")
    if not waiting:
        return

    text = (update.message.text or "").strip()
    if not text:
        return

    user = update.effective_user

    if waiting == "review":
        msg = (
            "⭐ *Yangi fikr*\n\n"
            f"👤 *Kimdan:* {user.full_name}\n"
            f"🆔 *User ID:* {user.id}\n"
            f"🕒 *Vaqt:* {now_str()}\n\n"
            f"💬 *Fikr:*\n{text}"
        )
        await send_to_admins(context.application, msg)
        await update.message.reply_text("✅ Fikringiz uchun rahmat! 🙏", reply_markup=ReplyKeyboardRemove())
        context.user_data.pop("waiting", None)
        return

    if waiting == "order":
        section_title = context.user_data.get("order_section_title", "Noma’lum bo‘lim")
        section_key = context.user_data.get("order_section_key", "unknown")

        msg = (
            "📦 *Yangi buyurtma / so‘rov*\n\n"
            f"🧩 *Bo‘lim:* {section_title}\n"
            f"🔑 *Key:* {section_key}\n"
            f"👤 *Mijoz:* {user.full_name}\n"
            f"🆔 *User ID:* {user.id}\n"
            f"🕒 *Vaqt:* {now_str()}\n\n"
            f"📝 *Xabar:*\n{text}"
        )
        await send_to_admins(context.application, msg)

        await update.message.reply_text(
            "✅ So‘rovingiz qabul qilindi!\nTez orada siz bilan bog‘lanamiz.",
            reply_markup=ReplyKeyboardRemove(),
        )

        context.user_data.pop("waiting", None)
        context.user_data.pop("order_section_title", None)
        context.user_data.pop("order_section_key", None)
        return


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q:
        return

    await q.answer()
    data = q.data or ""

    # --- ORQAGA ---
    if data == "back:main":
        context.user_data.pop("waiting", None)
        await q.message.edit_text(
            f"{BRAND_TITLE}\n\nXizmat turini tanlang 👇",
            reply_markup=main_menu_kb(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if data == "back:mebel":
        await q.message.edit_text(
            "🪑 *Mebel xizmati*\n\nKerakli bo‘limni tanlang 👇",
            reply_markup=mebel_menu_kb(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # --- XIZMATLAR ---
    if data.startswith("svc:"):
        svc = data.split(":", 1)[1]
        titles = {
            "konstruktor": "💻 *Konstruktlash xizmati*",
            "boyash": "🎨 *Bo‘yash xizmati*",
            "eshik": "🚪 *Eshiklar xizmati*",
            "ustalar": "🧑‍🔧 *Ustalar xizmati*",
        }
        if svc == "mebel":
            await q.message.edit_text(
                "🪑 *Mebel xizmati*\n\nKerakli bo‘limni tanlang 👇",
                reply_markup=mebel_menu_kb(),
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        title = titles.get(svc, "*Xizmat*")
        section_key = f"svc/{svc}"

        await q.message.edit_text(
            f"{title}\n\nKerakli tugmani tanlang 👇",
            reply_markup=section_actions_kb(section_key=section_key, back_to="back:main"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # --- MEBEL ICHKI ---
    if data.startswith("mebel:"):
        key = data.split(":", 1)[1]
        name_map = {
            "oshxona": "🍽 *Oshxona mebellari*",
            "holl": "🪑 *Holl mebellari*",
            "bolalar": "🧸 *Bolalar yotoqxonasi*",
            "shkaf": "🚪 *Shkaf-kupe*",
            "ofis": "🏢 *Ofis mebellari*",
        }
        title = name_map.get(key, "🪑 *Mebel bo‘limi*")
        section_key = f"mebel/{key}"

        await q.message.edit_text(
            f"{title}\n\nKerakli tugmani tanlang 👇",
            reply_markup=section_actions_kb(section_key=section_key, back_to="back:mebel"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # --- ALOQA ---
    if data == "contact":
        phones_text = "\n".join([f"📞 {p}" for p in PHONES])

        await q.message.edit_text(
            "📞 *Biz bilan bog‘lanish*\n\n"
            f"*Telefon:*\n{phones_text}\n\n"
            f"*Telegram:* {TG_USERNAME}\n"
            f"*Instagram:* {IG_USERNAME}\n\n"
            "📲 Telefon raqamingizni ulashish uchun tugmani bosing:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("📲 Telefon raqamni yuborish", callback_data="share_phone")],
                    [InlineKeyboardButton("⬅️ Orqaga", callback_data="back:main")],
                ]
            ),
        )
        return

    if data == "share_phone":
        kb = ReplyKeyboardMarkup(
            [[KeyboardButton("📲 Telefonimni yuborish", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await q.message.reply_text("📲 Telefon raqamingizni yuborish uchun tugmani bosing:", reply_markup=kb)
        return

    # --- FIKRLAR ---
    if data == "reviews":
        context.user_data["waiting"] = "review"
        await q.message.reply_text("⭐ Fikr-mulohazangizni yozib yuboring (1 ta xabar bilan):", reply_markup=ReplyKeyboardRemove())
        return

    # --- NARX SO‘RASH ---
    if data.startswith("ask:"):
        section_key = data.split(":", 1)[1]

        # sarlavha
        title = section_key
        if section_key.startswith("mebel/"):
            k = section_key.split("/", 1)[1]
            title = {
                "oshxona": "Oshxona mebellari",
                "holl": "Holl mebellari",
                "bolalar": "Bolalar yotoqxonasi",
                "shkaf": "Shkaf-kupe",
                "ofis": "Ofis mebellari",
            }.get(k, "Mebel bo‘limi")
        elif section_key.startswith("svc/"):
            k = section_key.split("/", 1)[1]
            title = {
                "konstruktor": "Konstruktlash xizmati",
                "boyash": "Bo‘yash xizmati",
                "eshik": "Eshiklar xizmati",
                "ustalar": "Ustalar xizmati",
            }.get(k, "Xizmat")

        context.user_data["waiting"] = "order"
        context.user_data["order_section_key"] = section_key
        context.user_data["order_section_title"] = title

        await q.message.reply_text(
            f"🧾 *Narx so‘rash — {title}*\n\n"
            "Iltimos, 1 ta xabar bilan yozing:\n"
            "1) Ismingiz\n"
            "2) Telefon raqamingiz\n"
            "3) Buyurtma (o‘lcham, model, rang, manzil)\n\n"
            "✅ Xabaringiz adminlarga boradi.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    # --- PORTFOLIO ---
    if data.startswith("pf:"):
        section_key = data.split(":", 1)[1]
        if section_key.startswith("mebel/"):
            k = section_key.split("/", 1)[1]
            await q.message.reply_text("🖼 Ish namunalari yuborilmoqda...")
            await send_portfolio(update, context, k)
            return

        await q.message.reply_text("⚠️ Hozircha bu bo‘lim uchun rasmlar qo‘shilmagan.")
        return


# =============== APP BUILD (Render app.py shuni import qiladi) ===============
def build_app() -> Application:
    if not TOKEN:
        raise RuntimeError("TOKEN yo‘q (.env yoki Render env ga qo‘ying)")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.CONTACT, on_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    return app


def main():
    app = build_app()
    print("🤖 BOT ISHLAYAPTI (POLLING)...")
    print("ADMIN_CHAT_IDS =", ADMIN_CHAT_IDS)
   