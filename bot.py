from __future__ import annotations

import os
from datetime import datetime
from typing import List, Optional, Tuple

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
    ADMIN_CHAT_IDS_RAW = os.getenv("ADMIN_ID", "").strip()
ADMIN_CHAT_IDS = parse_chat_ids(ADMIN_CHAT_IDS_RAW)

# ================ CONSTANTS (brands) =================
DOOR_BRANDS = ["Profildors", "VFD", "Estet", "AurumDoors"]
PAINT_BRANDS = ["Bitek", "Gench", "Polchem", "Palitra"]

# ================= HELPERS =================
def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


async def send_to_admins(bot_app: Application, text: str) -> None:
    if not ADMIN_CHAT_IDS:
        return
    for chat_id in ADMIN_CHAT_IDS:
        try:
            await bot_app.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            pass


def phone_request_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton("☎️ Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def set_after_contact(context: ContextTypes.DEFAULT_TYPE, back_cb: str) -> None:
    # Aloqa tugmasidan keyin qaytadigan joy
    context.user_data["after_contact_back"] = back_cb


def pop_after_contact(context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    return context.user_data.pop("after_contact_back", None)


def clear_flow(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("flow", None)
    context.user_data.pop("svc_key", None)
    context.user_data.pop("material", None)
    context.user_data.pop("room_size", None)
    context.user_data.pop("address", None)
    context.user_data.pop("phone", None)


def svc_title(svc_key: str) -> str:
    titles = {
        "mebel": "🪑 Mebel xizmati",
        "eshik": "🚪 Eshiklar xizmati",
        "boyash": "🎨 Bo‘yash xizmati",
        "konstruktor": "🖥️ Konstruktlash xizmati",
        "ustalar": "👷 Ustalar xizmati",
    }
    return titles.get(svc_key, "Xizmat")


# ================= KEYBOARDS =================
def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🪑 Mebel xizmati", callback_data="svc:mebel")],
            [InlineKeyboardButton("🚪 Eshiklar xizmati", callback_data="svc:eshik")],
            [InlineKeyboardButton("🎨 Bo‘yash xizmati", callback_data="svc:boyash")],
            [InlineKeyboardButton("🖥️ Konstruktlash xizmati", callback_data="svc:konstruktor")],
            [InlineKeyboardButton("👷 Ustalar xizmati", callback_data="svc:ustalar")],
        ]
    )


def back_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="back:main")]])


def mebel_menu_kb() -> InlineKeyboardMarkup:
    # skrinshotdagi format: Narx so'rash, Ish namunalari, Aloqa, Fikrlar, Orqaga
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🧾 Narx so‘rash", callback_data="price:mebel"),
                InlineKeyboardButton("🖼️ Ish namunalari", callback_data="samples:mebel"),
            ],
            [
                InlineKeyboardButton("📞 Aloqa", callback_data="contact:mebel"),
                InlineKeyboardButton("⭐ Fikrlar", callback_data="reviews"),
            ],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="back:main")],
        ]
    )


def eshik_menu_kb() -> InlineKeyboardMarkup:
    # Narx so‘rash, Brendlar, Aloqa, Orqaga
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🧾 Narx so‘rash", callback_data="price:eshik"),
                InlineKeyboardButton("🏷️ Brendlar", callback_data="brands:eshik"),
            ],
            [InlineKeyboardButton("📞 Aloqa", callback_data="contact:eshik")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="back:main")],
        ]
    )


def eshik_brands_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"🚪 {b}", callback_data=f"brand:eshik:{b}")]
        for b in DOOR_BRANDS
    ]
    rows.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="back:svc:eshik")])
    return InlineKeyboardMarkup(rows)


def eshik_brand_inner_kb(brand: str) -> InlineKeyboardMarkup:
    # Har bir brend ichida Aloqa bo‘lsin + Orqaga
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📞 Aloqa", callback_data=f"contact:eshik_brand:{brand}")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="back:brands:eshik")],
        ]
    )


def boyash_menu_kb() -> InlineKeyboardMarkup:
    # Faqat brendlar + orqaga (siz aytgandek)
    rows = [
        [InlineKeyboardButton(f"🎨 {b}", callback_data=f"brand:boyash:{b}")]
        for b in PAINT_BRANDS
    ]
    rows.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="back:main")])
    return InlineKeyboardMarkup(rows)


def boyash_brand_inner_kb(brand: str) -> InlineKeyboardMarkup:
    # Har bir brend ichida Narx so‘rash + Orqaga
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🧾 Narx so‘rash", callback_data="price:boyash")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="back:svc:boyash")],
        ]
    )


def konstruktor_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📦 3D modellar", callback_data="kons:3d")],
            [InlineKeyboardButton("📌 Mijozga bilishi shart", callback_data="kons:mustknow")],
            [InlineKeyboardButton("📞 Aloqa", callback_data="contact:konstruktor")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="back:main")],
        ]
    )


def ustalar_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🖼️ Ish namunalari", callback_data="samples:ustalar"),
                InlineKeyboardButton("🧾 Narx so‘rash", callback_data="price:ustalar"),
            ],
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
            [InlineKeyboardButton("⬅️ Orqaga", callback_data=f"back:svc:{svc_key}")],
        ]
    )


# ================= COMMANDS =================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    clear_flow(context)
    await update.message.reply_text(
        f"*{BRAND_TITLE}*\n\nXizmat turini tanlang 👇",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_kb(),
    )


# ================= CALLBACKS =================
async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    if not q or not q.message:
        return

    await q.answer()
    data = q.data or ""

    # -------- BACK ROUTER --------
    if data == "back:main":
        clear_flow(context)
        await q.message.edit_text(
            f"*{BRAND_TITLE}*\n\nXizmat turini tanlang 👇",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_kb(),
        )
        return

    if data.startswith("back:svc:"):
        svc_key = data.split(":", 2)[2]
        await show_service_menu(q, svc_key)
        return

    if data == "back:brands:eshik":
        await q.message.edit_text(
            "🏷️ *Eshik brendlari* — tanlang 👇",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=eshik_brands_kb(),
        )
        return

    # -------- REVIEWS --------
    if data == "reviews":
        await q.message.reply_text("⭐ Fikr-mulohazangizni 1 ta xabar qilib yozib yuboring:")
        context.user_data["flow"] = "review_text"
        return

    # -------- CONTACT (phone) --------
    if data.startswith("contact:"):
        # qaytish joyini belgilab qo'yamiz
        # contact:mebel / contact:eshik / contact:konstruktor / contact:eshik_brand:Profildors ...
        set_after_contact(context, back_cb=guess_back_callback(data))
        context.user_data["flow"] = "contact_phone"
        await q.message.reply_text(
            "☎️ Biz bilan bog‘lanish uchun telefon raqamingizni yuboring 👇",
            reply_markup=phone_request_kb(),
        )
        return

    # -------- SERVICE ENTER --------
    if data.startswith("svc:"):
        svc_key = data.split(":", 1)[1]
        await show_service_menu(q, svc_key)
        return

    # -------- SAMPLES --------
    if data.startswith("samples:"):
        svc_key = data.split(":", 1)[1]
        await q.message.reply_text(
            f"🖼️ *{svc_title(svc_key)} — ish namunalari*\n\n"
            "📌 Namuna (rasm/video/link) qo‘shish uchun ayting — qo‘shib beraman.\n"
            "Hozircha aloqa orqali so‘rashingiz mumkin.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_main_kb(),
        )
        return

    # -------- BRANDS MENU OPEN --------
    if data == "brands:eshik":
        await q.message.edit_text(
            "🏷️ *Eshik brendlari* — tanlang 👇",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=eshik_brands_kb(),
        )
        return

    # -------- BRAND OPEN --------
    if data.startswith("brand:"):
        # brand:{svc}:{name}
        _, svc, name = data.split(":", 2)
        if svc == "eshik":
            await q.message.edit_text(
                f"🚪 *{name}*\n\nKerakli tugmani tanlang 👇",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=eshik_brand_inner_kb(name),
            )
            return
        if svc == "boyash":
            await q.message.edit_text(
                f"🎨 *{name}*\n\nKerakli tugmani tanlang 👇",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=boyash_brand_inner_kb(name),
            )
            return

    # -------- KONSTRUKTOR MENU ITEMS --------
    if data == "kons:3d":
        await q.message.reply_text(
            "📦 *3D modellar*\n\n"
            "Bu bo‘limga 3D namuna/linklar qo‘shamiz.\n"
            "Qaysi format kerak: SketchUp, 3ds Max, Blender, yoki rasmlar?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=konstruktor_menu_kb(),
        )
        return

    if data == "kons:mustknow":
        await q.message.reply_text(
            "📌 *Mijozga bilishi shart*\n\n"
            "1) O‘lcham aniq bo‘lishi kerak\n"
            "2) Material turi (MDF/LMDF/Akril/Kraska)\n"
            "3) Manzil va muddat\n"
            "4) Dizayn/rasm bo‘lsa yuborish\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=konstruktor_menu_kb(),
        )
        return

    # -------- START PRICE FLOW --------
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

    # -------- MATERIAL CHOSEN --------
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


async def show_service_menu(q, svc_key: str) -> None:
    if svc_key == "mebel":
        await q.message.edit_text("Kerakli tugmani tanlang 👇", reply_markup=mebel_menu_kb())
        return
    if svc_key == "eshik":
        await q.message.edit_text("Kerakli tugmani tanlang 👇", reply_markup=eshik_menu_kb())
        return
    if svc_key == "boyash":
        await q.message.edit_text("Brendni tanlang 👇", reply_markup=boyash_menu_kb())
        return
    if svc_key == "konstruktor":
        await q.message.edit_text("Kerakli tugmani tanlang 👇", reply_markup=konstruktor_menu_kb())
        return
    if svc_key == "ustalar":
        await q.message.edit_text("Kerakli tugmani tanlang 👇", reply_markup=ustalar_menu_kb())
        return

    await q.message.edit_text("Kerakli tugmani tanlang 👇", reply_markup=back_main_kb())


def guess_back_callback(contact_cb: str) -> str:
    # Aloqa bosilgandan keyin qayerga qaytishni belgilash
    # contact:mebel -> back:svc:mebel
    # contact:eshik_brand:Profildors -> back:brands:eshik (brendlar listiga)
    if contact_cb.startswith("contact:eshik_brand:"):
        return "back:brands:eshik"
    if contact_cb.startswith("contact:"):
        svc = contact_cb.split(":", 1)[1]
        # mebel/eshik/konstruktor/ustalar
        return f"back:svc:{svc}"
    return "back:main"


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

        back_cb = pop_after_contact(context)
        clear_flow(context)

        # keyboardni yopamiz
        await update.message.reply_text("✅ Rahmat! Tez orada siz bilan bog‘lanamiz.", reply_markup=ReplyKeyboardRemove())

        # qaytish joyini inline bilan chiqaramiz
        if back_cb == "back:brands:eshik":
            await update.message.reply_text(
                "🏷️ *Eshik brendlari* — tanlang 👇",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=eshik_brands_kb(),
            )
        elif back_cb and back_cb.startswith("back:svc:"):
            svc_key = back_cb.split(":", 2)[2]
            # fake callback yo‘q, shunchaki menyuni yuboramiz
            if svc_key == "mebel":
                await update.message.reply_text("Kerakli tugmani tanlang 👇", reply_markup=mebel_menu_kb())
            elif svc_key == "eshik":
                await update.message.reply_text("Kerakli tugmani tanlang 👇", reply_markup=eshik_menu_kb())
            elif svc_key == "boyash":
                await update.message.reply_text("Brendni tanlang 👇", reply_markup=boyash_menu_kb())
            elif svc_key == "konstruktor":
                await update.message.reply_text("Kerakli tugmani tanlang 👇", reply_markup=konstruktor_menu_kb())
            elif svc_key == "ustalar":
                await update.message.reply_text("Kerakli tugmani tanlang 👇", reply_markup=ustalar_menu_kb())
            else:
                await update.message.reply_text("Xizmat turini tanlang 👇", reply_markup=main_menu_kb())
        else:
            await update.message.reply_text("Xizmat turini tanlang 👇", reply_markup=main_menu_kb())
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
        await update.message.reply_text("Xizmat turini tanlang 👇", reply_markup=main_menu_kb())
        return

    await update.message.reply_text("✅ Qabul qilindi.", reply_markup=ReplyKeyboardRemove())


# ================= BUILD APP =================
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
