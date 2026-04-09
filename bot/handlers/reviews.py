"""Rating and review flow."""
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CallbackQueryHandler,
    MessageHandler, filters
)
from db.models import SessionLocal
from db.queries import get_or_create_user, add_review, get_business
from bot.keyboards import rating_keyboard
from services.i18n import t

# States
COMMENT = range(1)


def _lang(telegram_id: int) -> str:
    db = SessionLocal()
    try:
        user = get_or_create_user(db, telegram_id, "")
        return user.language
    finally:
        db.close()


async def rate_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    biz_id = int(query.data.split(":")[1])
    lang = _lang(query.from_user.id)
    context.user_data["rate_biz_id"] = biz_id
    await query.message.reply_text(t("rate_prompt", lang), reply_markup=rating_keyboard(biz_id))


async def rating_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, biz_id, rating = query.data.split(":")
    context.user_data["rate_biz_id"] = int(biz_id)
    context.user_data["rate_value"] = int(rating)
    lang = _lang(query.from_user.id)
    await query.edit_message_text("💬 Add a comment (or type /skip):")
    return COMMENT


async def got_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    comment = None if text == "/skip" else text
    lang = _lang(update.effective_user.id)

    biz_id = context.user_data.get("rate_biz_id")
    rating = context.user_data.get("rate_value")

    db = SessionLocal()
    try:
        db_user = get_or_create_user(db, update.effective_user.id, update.effective_user.full_name)
        add_review(db, biz_id, db_user.id, rating, comment)
    finally:
        db.close()

    await update.message.reply_text(t("rate_saved", lang))
    return ConversationHandler.END


def get_review_conversation():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(rating_selected, pattern="^rating:\\d+:\\d+$")],
        states={
            COMMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_comment),
                MessageHandler(filters.COMMAND, got_comment),
            ],
        },
        fallbacks=[],
        per_message=False,
    )
