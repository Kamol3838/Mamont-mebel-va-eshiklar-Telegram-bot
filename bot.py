    # TEST CHANGE
from __future__ import annotations

import os
from datetime import datetime
from typing import List, Optional

from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
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

# ================= ENV =================
load_dotenv()

TOKEN = os.getenv("TOKEN", "").strip()
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip()

BRAND_TITLE = "🏠 Mamont mebel va eshiklar"


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


ADMIN_CHAT_IDS_RAW = os.getenv("ADMIN_CHAT_IDS", "").strip()
if not ADMIN_CHAT_IDS_RAW:
    # eski nom bilan yozib qo'ygan bo'lishi mumkin
    ADMIN_CHAT_IDS_RAW = os.getenv("ADMIN_ID", "").strip()

ADMIN_CHAT_IDS = parse_chat_ids(ADMIN_CHAT_IDS_RAW)

# ================= HELPERS =================
def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


async def send_to_admins(bot_app: Application, text: str) -> None:
    for chat_id in ADMIN_CHAT_IDS:
        try:
            await bot_app.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            # xatoni yutib yuboramiz, bot yiqilmasin
            pass


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🪑 Mebel xizmati", callback_data="svc:mebel")],
            [InlineKeyboardButton("🚪 Eshiklar xizmati", callback_data="svc:eshik")],
            [InlineKeyboardButton("🎨 Bo‘yash xizmati", callback_data="svc:boyash")],
            [InlineKeyboardButton("🖥️ Konstruktlash xizmati", callback_data="svc:konstruktor")],
            [InlineKeyboardButton("👷 Ustalar xizmati", callback_data="svc:ustalar")],
            [
                InlineKeyboardButton("☎️ Aloqa", callback_data="contact"),
                InlineKeyboardButton("⭐ Fikrlar", callback_data="reviews"),
            ],
        ]
    )


def service_actions_kb(svc_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("💰 Narx so‘rash", callback_data=f"price:{svc_key}")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="back:main")],
        ]
    )


def materials_kb(svc_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📦 MDF", callback_data=f"mat:{svc_key}:MDF"),
                InlineKeyboardButton("📦 LMDF", callback_data=f"mat:{svc_key}:LMDF"),
            ],
            [
                InlineKeyboardButton("📦 Akril", callback_data=f"mat:{svc_key}:Akril"),
                InlineKeyboardButton("🎨 Kraska", callback_data=f"mat:{svc_key}:Kraska"),
            ],
            [InlineKeyboardButton("✍️ O‘zim yozaman", callback_data=f"mat:{svc_key}:OTHER")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data=f"svc:{svc_key}")],
        ]
    )


def phone_request_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton("☎️ Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def svc_title(svc_key: str) -> str:
    titles = {
        "mebel": "🪑 Mebel xizmati",
        "eshik": "🚪 Eshiklar xizmati",
        "boyash": "🎨 Bo‘yash xizmati",
        "konstruktor": "🖥️ Konstruktlash xizmati",
        "ustalar": "👷 Ustalar xizmati",
    }
    return titles.get(svc_key, "Xizmat")


def clear_flow(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("flow", None)
    context.user_data.pop("svc_key", None)
    context.user_data.pop("material", None)
    context.user_data.pop("room_size", None)
    context.user_data.pop("address", None)
    context.user_data.pop("phone", None)


# ================= COMMANDS =================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"{BRAND_TITLE}\n\nXizmat turini tanlang 👇",
        reply_markup=main_menu_kb(),
        parse_mode=ParseMode.MARKDOWN
    )



# ================= CALLBACKS =================
async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    if not q:
        return

    await q.answer()
    data = q.data or ""

    # ---- BACK ----
    if data == "back:main":
        clear_flow(context)
        await q.message.edit_text(
            f"*{BRAND_TITLE}*\n\nXizmat turini tanlang 👇",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_kb(),
        )
        return

    # ---- REVIEWS ----
    if data == "reviews":
        await q.message.reply_text("⭐ Fikr-mulohazangizni 1 ta xabar qilib yozib yuboring:")
        context.user_data["flow"] = "review_text"
        return

    # ---- CONTACT (telefonni 1 bosishda) ----
    if data == "contact":
        context.user_data["flow"] = "contact_phone"
        await q.message.reply_text(
            "☎️ Biz bilan bog‘lanish uchun telefon raqamingizni yuboring 👇",
            reply_markup=phone_request_kb(),
        )
        return

    # ---- SERVICE ----
    if data.startswith("svc:"):
        svc_key = data.split(":", 1)[1]
        title = svc_title(svc_key)
        await q.message.edit_text(
            f"{title}\n\nKerakli bo‘limni tanlang 👇",
            reply_markup=service_actions_kb(svc_key),
        )
        return

    # ---- START PRICE FLOW ----
    if data.startswith("price:"):
        svc_key = data.split(":", 1)[1]
        context.user_data["flow"] = "price_material"
        context.user_data["svc_key"] = svc_key
        await q.message.reply_text(
            f"💰 *Narx so‘rash* — {svc_title(svc_key)}\n\n📦 Materialni tanlang 👇",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=materials_kb(svc_key),
        )
        return

    # ---- MATERIAL CHOSEN ----
    if data.startswith("mat:"):
        # mat:{svc_key}:{MDF/LMDF/Akril/Kraska/OTHER}
        _, svc_key, mat = data.split(":", 2)
        context.user_data["svc_key"] = svc_key

        if mat == "OTHER":
            context.user_data["flow"] = "price_material_other"
            await q.message.reply_text("✍️ Materialni yozing (masalan: shpon, fanera, ...):")
            return

        context.user_data["material"] = mat
        context.user_data["flow"] = "price_room"
        await q.message.reply_text("📏 Xona (yoki mebel) o‘lchamini yozing (masalan: 3.2x4.1 yoki 12 m²):")
        return


# ================= TEXT HANDLER (flow) =================
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    flow = context.user_data.get("flow")
    text = (update.message.text or "").strip()
    user = update.effective_user

    if not flow:
        return

    # ---- REVIEW TEXT ----
    if flow == "review_text":
        msg = (
            "⭐ *Yangi fikr*\n\n"
            f"👤 *Kimdan:* {user.full_name}\n"
            f"🆔 *User ID:* `{user.id}`\n"
            f"🕒 *Vaqt:* {now_str()}\n\n"
            f"💬 *Fikr:*\n{text}"
        )
        await send_to_admins(context.application, msg)
        clear_flow(context)
        await update.message.reply_text("✅ Rahmat! Fikringiz qabul qilindi.", reply_markup=ReplyKeyboardRemove())
        return

    # ---- MATERIAL OTHER ----
    if flow == "price_material_other":
        context.user_data["material"] = text
        context.user_data["flow"] = "price_room"
        await update.message.reply_text("📏 Xona (yoki mebel) o‘lchamini yozing (masalan: 3.2x4.1 yoki 12 m²):")
        return

    # ---- ROOM SIZE ----
    if flow == "price_room":
        context.user_data["room_size"] = text
        context.user_data["flow"] = "price_address"
        await update.message.reply_text("📍 Manzilingizni yozing (tuman/shahar + mo‘ljal):")
        return

    # ---- ADDRESS ----
    if flow == "price_address":
        context.user_data["address"] = text
        context.user_data["flow"] = "price_phone"
        await update.message.reply_text(
            "☎️ Telefon raqamingizni 1 bosishda yuboring 👇",
            reply_markup=phone_request_kb(),
        )
        return


# ================= CONTACT HANDLER =================
async def on_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.contact:
        return

    contact = update.message.contact
    user = update.effective_user
    phone = contact.phone_number

    flow = context.user_data.get("flow")

    # ---- CONTACT BUTTON FLOW ----
    if flow == "contact_phone":
        msg = (
            "☎️ *Yangi aloqa so‘rovi*\n\n"
            f"👤 *Ism:* {user.full_name}\n"
            f"🆔 *User ID:* `{user.id}`\n"
            f"📞 *Telefon:* `{phone}`\n"
            f"🧾 *Username:* @{user.username if user.username else 'yo‘q'}\n"
            f"🕒 *Vaqt:* {now_str()}"
        )
        await send_to_admins(context.application, msg)
        clear_flow(context)
        await update.message.reply_text("✅ Rahmat! Tez orada siz bilan bog‘lanamiz.", reply_markup=ReplyKeyboardRemove())
        return

    # ---- PRICE FLOW (final step) ----
    if flow == "price_phone":
        svc_key = context.user_data.get("svc_key", "unknown")
        material = context.user_data.get("material", "yo‘q")
        room_size = context.user_data.get("room_size", "yo‘q")
        address = context.user_data.get("address", "yo‘q")

        msg = (
            "💰 *Narx so‘rash (to‘liq buyurtma)*\n\n"
            f"🛠 *Xizmat:* {svc_title(svc_key)}\n"
            f"📦 *Material:* `{material}`\n"
            f"📏 *O‘lcham:* `{room_size}`\n"
            f"📍 *Manzil:* {address}\n\n"
            f"👤 *Mijoz:* {user.full_name}\n"
            f"🆔 *User ID:* `{user.id}`\n"
            f"📞 *Telefon:* `{phone}`\n"
            f"🧾 *Username:* @{user.username if user.username else 'yo‘q'}\n"
            f"🕒 *Vaqt:* {now_str()}"
        )

        await send_to_admins(context.application, msg)
        clear_flow(context)
        await update.message.reply_text(
            "✅ So‘rovingiz yuborildi! Tez orada siz bilan bog‘lanamiz.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    # Agar flow boshqa bo'lsa ham keyboardni yopamiz
    await update.message.reply_text("✅ Qabul qilindi.", reply_markup=ReplyKeyboardRemove())


# ================= BUILD APP (Render app.py shu yerda ishlatadi) =================
def build_app() -> Application:
    if not TOKEN:
        raise RuntimeError("TOKEN yo‘q (.env yoki Render env ga qo‘ying)")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.CONTACT, on_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    return app


# ================= LOCAL RUN (polling) =================
def main() -> None:
    app = build_app()
    print("✅ Bot ishga tushdi (polling)...")
    app.run_polling(close_loop=False)


if __name__ == "__main__":
    main()
