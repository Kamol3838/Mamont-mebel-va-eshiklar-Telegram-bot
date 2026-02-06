import os
from datetime import datetime
from pathlib import Path

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
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

load_dotenv()

TOKEN = os.getenv("TOKEN")

# Render/Local .env dan: 1469..., -1003... kabi
ADMIN_CHAT_IDS_RAW = os.getenv("ADMIN_CHAT_IDS", "")

def parse_chat_ids(raw: str) -> list[int]:
    ids: list[int] = []
    for part in (raw or "").replace("\n", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.append(int(part))
        except ValueError:
            pass
    return ids

ADMIN_CHAT_IDS = parse_chat_ids(ADMIN_CHAT_IDS_RAW)

print("ADMIN_CHAT_IDS =", ADMIN_CHAT_IDS)  # tekshiruv uchun



BRAND_TITLE = "🏠 Mamont mebel va eshiklar"

PHONES = ["+998946103838", "+998906144440"]
TG_USERNAME = "@bazizbuxara"
IG_USERNAME = "@jumayev1992"

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"

# Portfoliodagi rasmlar nomlari (images/ ichida bo‘lishi kerak)
PORTFOLIO = {
    "oshxona": ["oshxona1.jpg", "oshxona2.jpg", "oshxona3.jpg"],
    "holl": ["holl1.jpg", "holl2.jpg", "holl3.jpg"],
    "bolalar": ["bolalar1.jpg", "bolalar2.jpg", "bolalar3.jpg"],
    "shkaf": ["shkaf1.jpg", "shkaf2.jpg", "shkaf3.jpg"],
    "ofis": ["ofis1.jpg", "ofis2.jpg", "ofis3.jpg"],
}

WORK_TIME_TEXT = (
    "⏰ *Ish vaqti:*\n"
    "Dushanba–Shanba: 09:00 – 19:00\n"
    "Yakshanba: 10:00 – 16:00"
)


def parse_admin_ids(raw: str) -> list[int]:
    """
    ADMIN_CHAT_IDS=1469,-1003 kabi bo‘ladi.
    Verguldan keyin probel bo‘lsa ham ishlaydi.
    """
    ids: list[int] = []
    for x in raw.split(","):
        x = x.strip()
        if not x:
            continue
        try:
            ids.append(int(x))
        except ValueError:
            pass
    return ids


ADMIN_CHAT_IDS = parse_admin_ids(ADMIN_CHAT_IDS_RAW)


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🪑 Mebel xizmati", callback_data="svc:mebel")],
            [InlineKeyboardButton("🚪 Eshiklar xizmati", callback_data="svc:eshik")],
            [InlineKeyboardButton("🎨 Bo‘yash xizmati", callback_data="svc:boyash")],
            # Siz so‘ragan: konstruktorlash kompyuter emojisi
            [InlineKeyboardButton("🖥️ Konstruktrlash xizmati", callback_data="svc:konstruktor")],
            [InlineKeyboardButton("👷 Ustalar xizmati", callback_data="svc:ustalar")],
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
            [InlineKeyboardButton("🛋 Holl", callback_data="mebel:holl")],
            [InlineKeyboardButton("🧸 Bolalar yotoqxonasi", callback_data="mebel:bolalar")],
            [InlineKeyboardButton("🚪 Shkaf-kupe", callback_data="mebel:shkaf")],
            [InlineKeyboardButton("🧑‍💻 Ofis mebellari", callback_data="mebel:ofis")],
            [InlineKeyboardButton("⬅ Orqaga", callback_data="back:main")],
        ]
    )


def section_actions_kb(section_key: str, back_to: str) -> InlineKeyboardMarkup:
    """
    section_key: 'mebel/oshxona' yoki 'svc/eshik' kabi
    back_to: 'back:main' yoki 'back:mebel'
    """
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
            [InlineKeyboardButton("⬅ Orqaga", callback_data=back_to)],
        ]
    )


async def send_to_admins(app, text: str) -> None:
    if not ADMIN_CHAT_IDS:
        # admin id lar yo‘q bo‘lsa jim turamiz
        return
    for chat_id in ADMIN_CHAT_IDS:
        try:
            await app.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            pass


async def send_portfolio(update: Update, key: str) -> None:
    files = PORTFOLIO.get(key, [])
    sent_any = False

    for fn in files:
        path = IMAGES_DIR / fn
        if path.exists() and path.is_file():
            sent_any = True
            await update.effective_chat.send_photo(photo=InputFile(path))

    if not sent_any:
        await update.effective_chat.send_message(
            "🖼 Hozircha bu bo‘limga rasmlar qo‘shilmagan.\n"
            "✅ images/ papkaga rasmlarni qo‘ying va PORTFOLIO ro‘yxatini moslang."
        )


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🏠 *Mamont mebel va eshiklar*\n\nXizmat turini tanlang 👇",
        reply_markup=main_menu_kb(),
        parse_mode=ParseMode.MARKDOWN,
    )


async def on_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.contact:
        return

    c = update.message.contact
    user = update.effective_user
    phone = c.phone_number or "Noma’lum"

    msg = (
        "📞 *Mijoz telefon ulashdi*\n\n"
        f"👤 *Mijoz:* {user.full_name}\n"
        f"🆔 *User ID:* {user.id}\n"
        f"📱 *Telefon:* {phone}\n"
        f"🕒 *Vaqt:* {now_str()}"
    )
    await send_to_admins(context.application, msg)

    await update.message.reply_text(
        "✅ Rahmat! Telefon raqamingiz qabul qilindi.",
        reply_markup=ReplyKeyboardRemove(),
    )


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    waiting = context.user_data.get("waiting")
    if not waiting or not update.message:
        return

    text = (update.message.text or "").strip()
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

    # ORQAGA
    if data == "back:main":
        await q.message.edit_text(
            f"🏠 *Mamont mebel va eshiklar*\n\nXizmat turini tanlang 👇",
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

    # XIZMATLAR (main menyudan)
    if data.startswith("svc:"):
        svc = data.split(":", 1)[1]

        titles = {
            "mebel": "🪑 *Mebel xizmati*",
            "eshik": "🚪 *Eshiklar xizmati*",
            "boyash": "🎨 *Bo‘yash xizmati*",
            "konstruktor": "🖥️ *Konstruktrlash xizmati*",
            "ustalar": "👷 *Ustalar xizmati*",
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

    # MEBEL ICHKI
    if data.startswith("mebel:"):
        key = data.split(":", 1)[1]
        name_map = {
            "oshxona": "🍽 *Oshxona mebellari*",
            "holl": "🛋 *Holl mebellari*",
            "bolalar": "🧸 *Bolalar yotoqxonasi*",
            "shkaf": "🚪 *Shkaf-kupe*",
            "ofis": "🧑‍💻 *Ofis mebellari*",
        }
        title = name_map.get(key, "🪑 *Mebel bo‘limi*")
        section_key = f"mebel/{key}"

        await q.message.edit_text(
            f"{title}\n\nKerakli tugmani tanlang 👇",
            reply_markup=section_actions_kb(section_key=section_key, back_to="back:mebel"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # ALOQA
    if data == "contact":
        phones_text = "\n".join([f"📱 {p}" for p in PHONES])
        await q.message.edit_text(
            "📞 *Biz bilan bog‘lanish*\n\n"
            f"*Telefon:*\n{phones_text}\n\n"
            f"*Telegram:* {TG_USERNAME}\n"
            f"*Instagram:* {IG_USERNAME}\n\n"
            f"{WORK_TIME_TEXT}\n\n"
            "📲 Telefon raqamingizni yuborish uchun tugmani bosing:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("📲 Telefon raqamini yuborish", callback_data="share_phone")],
                    [InlineKeyboardButton("⬅ Orqaga", callback_data="back:main")],
                ]
            ),
        )
        return

    # TELEFON ULASHISH
    if data == "share_phone":
        kb = ReplyKeyboardMarkup(
            [[KeyboardButton("📲 Telefonimni yuborish", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await q.message.reply_text("📲 Telefon raqamingizni yuborish uchun tugmani bosing:", reply_markup=kb)
        return

    # FIKRLAR
    if data == "reviews":
        context.user_data["waiting"] = "review"
        await q.message.reply_text(
            "⭐ Fikr-mulohazangizni yozib yuboring (1 ta xabar bilan):",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    # NARX SO‘RASH
    if data.startswith("ask:"):
        section_key = data.split(":", 1)[1]

        # chiroyli title chiqaramiz
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
                "mebel": "Mebel xizmati",
                "eshik": "Eshiklar xizmati",
                "boyash": "Bo‘yash xizmati",
                "konstruktor": "Konstruktrlash xizmati",
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

    # PORTFOLIO
    if data.startswith("pf:"):
        section_key = data.split(":", 1)[1]
        if section_key.startswith("mebel/"):
            k = section_key.split("/", 1)[1]
            await q.message.reply_text("🖼 Ish namunalari yuborilmoqda...")
            await send_portfolio(update, k)
        else:
            await q.message.reply_text("🖼 Hozircha bu xizmat uchun rasmlar qo‘shilmagan.")
        return


def main():
    if not TOKEN:
        raise RuntimeError("TOKEN yo‘q (.env ga qo‘ying)")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.CONTACT, on_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    print("Bot ishga tushdi (polling)...")
    app.run_polling()


if __name__ == "__main__":
    main()
