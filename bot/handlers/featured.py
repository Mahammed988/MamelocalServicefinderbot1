from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from db.models import SessionLocal
from db.queries import get_or_create_user, search_businesses
from bot.keyboards import business_card_keyboard, main_menu_keyboard
from bot.formatters import format_business_card
from services.i18n import t


async def featured_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = SessionLocal()
    try:
        db_user = get_or_create_user(db, user.id, user.full_name)
        lang = db_user.language
        from sqlalchemy import and_
        from db.models import Business
        rows = (
            db.query(Business)
            .filter(and_(Business.is_featured == True, Business.is_approved == True))
            .all()
        )
        # Snapshot to dicts before session closes
        businesses = [
            {
                "id": b.id, "name": b.name, "category": b.category,
                "latitude": b.latitude, "longitude": b.longitude,
                "area_name": b.area_name, "phone": b.phone,
                "telegram_username": b.telegram_username, "whatsapp": b.whatsapp,
                "description": b.description, "is_featured": b.is_featured,
                "is_open": b.is_open,
            }
            for b in rows
        ]
    finally:
        db.close()

    if not businesses:
        await update.message.reply_text("⭐ No featured services at the moment.")
        return

    await update.message.reply_text(
        f"⭐ *Featured Services* ({len(businesses)} listings)",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(lang),
    )

    for biz in businesses:
        text = format_business_card(biz, lang=lang)
        kb = business_card_keyboard(
            biz["id"], biz["phone"], biz["telegram_username"], biz["whatsapp"],
            lat=biz["latitude"], lon=biz["longitude"],
        )
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)


def get_handlers():
    return [
        MessageHandler(filters.Regex("^⭐ Featured Services$"), featured_services),
    ]
