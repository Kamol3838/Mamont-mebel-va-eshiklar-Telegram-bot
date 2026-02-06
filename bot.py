import os
from datetime import datetime
from typing import List

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
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

load_dotenv()

TOKEN = os.getenv("TOKEN", "")
ADMIN_CHAT_IDS_RAW = os.getenv("ADMIN_CHAT_IDS", "").strip()


def parse_chat_ids(raw: str) -> List[int]:
    ids: List[int] = []
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


# ===== helpers =====
def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🪑 Mebel xizmati", callback_data="svc:mebel")],
            [InlineKeyboardButton("🚪 Eshiklar xizmati", callback_data="svc:eshik")],
            [InlineKeyboardButton("🎨 Bo‘yash xizmati", callback_data="svc:boyash")],
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
            [InlineKeyboardButton("🏢 Ofis mebellari", callback_data="mebel:ofis")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="back:main")],
        ]
    )


def section_actions_kb(section_key: str, back_to: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📝 Narx so‘rash", callback_data=f"ask:{section_key}"),
                InlineKeyboardButton("🖼 Ish namunalari", callback_data=f"pf:{section_key}"),
            ],
            [
                InlineKeyboardButton("📞 Aloqa", callback_data="contact"),
                InlineKeyboardButton("⭐ Fikrlar", callback_data="reviews"),
            ],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data=back_to)],
        ]
    )


def phone_request_kb() -> ReplyKeyboardMarkup:
    # 1 martalik telefon yuborish tugmasi
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📲 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def materials_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("MDF", callback_data="mat:MDF"),
                InlineKeyboardButton("LMDF", callback_data="mat:LMDF"),
            ],
            [
                InlineKeyboardButton("Akril", callback_data="mat:AKRIL"),
                InlineKeyboardButton("Kraska", callback_data="mat:KRASKA"),
            ],
            [InlineKeyboardButton("✍️ O‘zim yozaman", callback_data="mat:CUSTOM")],
        ]
    )


async def send_to_admins(app, text: str) -> None:
    if not ADMIN_CHAT_IDS:
        print("⚠️ ADMIN_CHAT_IDS bo‘sh. .env/Render env ni tekshiring.")
        return

    for chat_id in ADMIN_CHAT_IDS:
        try:
            await app.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            print(f"❌ Admin/gruppaga yuborilmadi chat_id={chat_id}: {e}")


def build_order_message(user, data: dict) -> str:
    return (
        "📦 *Yangi buyurtma / so‘rov*\n"
        f"🧩 *Bo‘lim:* {data.get('section_title','-')}\n"
        f"🔑 *Key:* {data.get('section_key','-')}\n"
        f"👤 *Mijoz:* {user.full_name}\n"
        f"🆔 *User ID:* {user.id}\n"
        f"📞 *Telefon:* {data.get('phone','-')}\n"
        f"📍 *Manzil:* {data.get('address','-')}\n"
        f"🧱 *Material:* {data.get('material','-')}\n"
        f"📐 *Xona o‘lchami:* {data.get('size','-')}\n"
        f"🕒 *Vaqt:* {now_str()}\n\n"
        f"📝 *Izoh:* \n{data.get('note','-')}"
    )


# ===== handlers =====
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"{BRAND_TITLE}\n\nXizmat turini tanlang 👇",
        reply_markup=main_menu_kb(),
        parse_mode=ParseMode.MARKDOWN,
    )


async def on_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.contact:
        return

    user = update.effective_user
    phone = update.message.contact.phone_number

    waiting = context.user_data.get("waiting")

    # 1) Narx so‘rashdagi telefon bosqichi
    if waiting == "order_phone":
        order = context.user_data.get("order", {})
        order["phone"] = phone
        context.user_data["order"] = order

        context.user_data["waiting"] = "order_address"
        await update.message.reply_text(
            "📍 *Manzilingizni yozing* (tuman/shahar, ko‘cha, orientir):",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    # 2) Aloqa bo‘limidan telefon yuborish
    if waiting == "contact_share":
        msg = (
            "📞 *Aloqa uchun telefon yuborildi*\n"
            f"👤 *Mijoz:* {user.full_name}\n"
            f"🆔 *User ID:* {user.id}\n"
            f"📞 *Telefon:* {phone}\n"
            f"🕒 *Vaqt:* {now_str()}"
        )
        await send_to_admins(context.application, msg)

        context.user_data.pop("waiting", None)
        await update.message.reply_text(
            "✅ Rahmat! Telefon raqamingiz adminlarga yuborildi.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    # boshqa holatlarda ham foydali: shunchaki rahmat
    await update.message.reply_text("✅ Rahmat!", reply_markup=ReplyKeyboardRemove())


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    waiting = context.user_data.get("waiting")
    if not waiting:
        return

    text = (update.message.text or "").strip()
    user = update.effective_user

    # ----- review -----
    if waiting == "review":
        msg = (
            "⭐ *Yangi fikr*\n"
            f"👤 *Kimdan:* {user.full_name}\n"
            f"🆔 *User ID:* {user.id}\n"
            f"🕒 *Vaqt:* {now_str()}\n\n"
            f"💬 *Fikr:* \n{text}"
        )
        await send_to_admins(context.application, msg)
        await update.message.reply_text("✅ Fikringiz uchun rahmat! 🙏", reply_markup=ReplyKeyboardRemove())
        context.user_data.pop("waiting", None)
        return

    # ----- order flow -----
    if waiting == "order_phone":
        # Agar odam baribir qo‘lda yozsa ham qabul qilamiz
        digits = "".join(ch for ch in text if ch.isdigit() or ch == "+")
        if len(digits.replace("+", "")) < 9:
            await update.message.reply_text(
                "📲 Telefonni tugma orqali yuboring yoki raqamingizni to‘liq yozing.",
                reply_markup=phone_request_kb(),
            )
            return

        order = context.user_data.get("order", {})
        order["phone"] = digits
        context.user_data["order"] = order

        context.user_data["waiting"] = "order_address"
        await update.message.reply_text(
            "📍 *Manzilingizni yozing* (tuman/shahar, ko‘cha, orientir):",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    if waiting == "order_address":
        order = context.user_data.get("order", {})
        order["address"] = text
        context.user_data["order"] = order

        context.user_data["waiting"] = "order_material"
        await update.message.reply_text(
            "🧱 *Materialni tanlang:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=ReplyKeyboardRemove(),
        )
        # material tanlash inline bo‘ladi
        await update.message.reply_text("👇", reply_markup=materials_kb())
        return

    if waiting == "order_material_custom":
        order = context.user_data.get("order", {})
        order["material"] = text
        context.user_data["order"] = order

        context.user_data["waiting"] = "order_size"
        await update.message.reply_text(
            "📐 *Xona o‘lchamini yozing* (masalan: 3x4m yoki 12m²):",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if waiting == "order_size":
        order = context.user_data.get("order", {})
        order["size"] = text
        context.user_data["order"] = order

        context.user_data["waiting"] = "order_note"
        await update.message.reply_text(
            "📝 *Qo‘shimcha izoh* (ixtiyoriy). Yo‘q bo‘lsa `-` yozing:",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if waiting == "order_note":
        order = context.user_data.get("order", {})
        order["note"] = text
        context.user_data["order"] = order

        # yuboramiz
        msg = build_order_message(user, order)
        await send_to_admins(context.application, msg)

        await update.message.reply_text(
            "✅ So‘rovingiz qabul qilindi!\nTez orada bog‘lanamiz.",
            reply_markup=ReplyKeyboardRemove(),
        )

        # tozalash
        context.user_data.pop("waiting", None)
        context.user_data.pop("order", None)
        return


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data or ""

    if data == "back:main":
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

    if data.startswith("svc:"):
        svc = data.split(":", 1)[1]

        if svc == "mebel":
            await q.message.edit_text(
                "🪑 *Mebel xizmati*\n\nKerakli bo‘limni tanlang 👇",
                reply_markup=mebel_menu_kb(),
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        titles = {
            "konstruktor": "🖥️ Konstruktrlash xizmati",
            "boyash": "🎨 Bo‘yash xizmati",
            "eshik": "🚪 Eshiklar xizmati",
            "ustalar": "👷 Ustalar xizmati",
        }
        title = titles.get(svc, "Xizmat")
        section_key = f"svc/{svc}"

        await q.message.edit_text(
            f"{title}\n\nKerakli tugmani tanlang 👇",
            reply_markup=section_actions_kb(section_key=section_key, back_to="back:main"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if data.startswith("mebel:"):
        key = data.split(":", 1)[1]
        name_map = {
            "oshxona": "🍽 *Oshxona mebellari*",
            "holl": "🛋 *Holl mebellari*",
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

    if data == "contact":
        phones_text = "\n".join([f"📞 `{p}`" for p in PHONES])

        kb = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📲 Telefon raqamni yuborish", callback_data="share_phone")],
                [InlineKeyboardButton("⬅️ Orqaga", callback_data="back:main")],
            ]
        )

        await q.message.edit_text(
            "📞 *Biz bilan bog‘lanish*\n\n"
            f"*Telefon:*\n{phones_text}\n\n"
            f"*Telegram:* {TG_USERNAME}\n"
            f"*Instagram:* {IG_USERNAME}\n\n"
            "✅ Telefon raqamingizni yuborsangiz adminlar darhol ko‘radi.",
            reply_markup=kb,
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if data == "share_phone":
        context.user_data["waiting"] = "contact_share"
        await q.message.reply_text(
            "📲 Telefon raqamingizni yuborish uchun tugmani bosing:",
            reply_markup=phone_request_kb(),
        )
        return

    if data == "reviews":
        context.user_data["waiting"] = "review"
        await q.message.reply_text(
            "⭐ Fikr-mulohazangizni yozib yuboring (1 ta xabar bilan):",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    if data.startswith("ask:"):
        section_key = data.split(":", 1)[1]

        # bo‘lim title
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
                "konstruktor": "Konstruktrlash xizmati",
                "boyash": "Bo‘yash xizmati",
                "eshik": "Eshiklar xizmati",
                "ustalar": "Ustalar xizmati",
            }.get(k, "Xizmat")

        # order init
        context.user_data["order"] = {
            "section_key": section_key,
            "section_title": title,
            "phone": "",
            "address": "",
            "material": "",
            "size": "",
            "note": "",
        }

        context.user_data["waiting"] = "order_phone"
        await q.message.reply_text(
            f"📝 *Narx so‘rash — {title}*\n\n"
            "📲 Avval telefon raqamingizni yuboring:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=phone_request_kb(),
        )
        return

    if data.startswith("mat:"):
        mat = data.split(":", 1)[1]
        if context.user_data.get("waiting") not in ("order_material", "order_material_custom"):
            # noto‘g‘ri holatda bosilgan bo‘lsa ham muloyim qaytamiz
            await q.message.reply_text("Material tanlash faqat buyurtma vaqtida ishlaydi.")
            return

        if mat == "CUSTOM":
            context.user_data["waiting"] = "order_material_custom"
            await q.message.reply_text("✍️ Materialni o‘zingiz yozing:")
            return

        # tanlangan material
        order = context.user_data.get("order", {})
        order["material"] = mat
        context.user_data["order"] = order

        context.user_data["waiting"] = "order_size"
        await q.message.reply_text(
            "📐 *Xona o‘lchamini yozing* (masalan: 3x4m yoki 12m²):",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if data.startswith("pf:"):
        await q.message.reply_text("🖼 Hozircha bu bo‘lim uchun rasmlar qo‘shilmagan.")
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
