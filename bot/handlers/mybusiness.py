"""Business owner dashboard."""
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from db.models import SessionLocal
from db.queries import (
    get_or_create_user, get_businesses_by_owner,
    get_business, update_business, delete_business
)
from bot.keyboards import my_business_keyboard, main_menu_keyboard, cancel_keyboard
from bot.formatters import format_business_card
from services.i18n import t

# States
EDIT_VALUE = range(1)


def _lang(telegram_id: int) -> str:
    db = SessionLocal()
    try:
        user = get_or_create_user(db, telegram_id, "")
        return user.language
    finally:
        db.close()


async def my_business(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = _lang(user.id)
    db = SessionLocal()
    try:
        businesses = get_businesses_by_owner(db, user.id)
        if not businesses:
            await update.message.reply_text(t("no_business", lang))
            return

        for biz in businesses:
            status = "✅ Approved" if biz.is_approved else "⏳ Pending Approval"
            text = format_business_card(biz, lang=lang) + f"\n\n{status}"
            kb = my_business_keyboard(biz.id, biz.is_open)
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)
    finally:
        db.close()


async def toggle_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, _, biz_id = query.data.split(":")
    biz_id = int(biz_id)

    db = SessionLocal()
    try:
        biz = get_business(db, biz_id)
        if not biz or biz.owner_telegram_id != query.from_user.id:
            await query.answer("⛔ Not authorized.", show_alert=True)
            return
        biz = update_business(db, biz_id, is_open=not biz.is_open)
        lang = _lang(query.from_user.id)
        text = format_business_card(biz, lang=lang)
        kb = my_business_keyboard(biz.id, biz.is_open)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=kb)
    finally:
        db.close()


async def edit_field_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, field, biz_id = query.data.split(":")
    context.user_data["edit_field"] = field
    context.user_data["edit_biz_id"] = int(biz_id)

    prompts = {"name": "✏️ Enter new business name:", "phone": "📞 Enter new phone number:"}
    await query.message.reply_text(prompts.get(field, "Enter new value:"), reply_markup=cancel_keyboard())
    return EDIT_VALUE


async def edit_field_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "❌ Cancel":
        lang = _lang(update.effective_user.id)
        await update.message.reply_text(t("main_menu", lang), reply_markup=main_menu_keyboard(lang))
        return ConversationHandler.END

    field = context.user_data.get("edit_field")
    biz_id = context.user_data.get("edit_biz_id")
    lang = _lang(update.effective_user.id)

    db = SessionLocal()
    try:
        biz = get_business(db, biz_id)
        if not biz or biz.owner_telegram_id != update.effective_user.id:
            await update.message.reply_text("⛔ Not authorized.")
            return ConversationHandler.END
        update_business(db, biz_id, **{field: text})
    finally:
        db.close()

    await update.message.reply_text("✅ Updated!", reply_markup=main_menu_keyboard(lang))
    return ConversationHandler.END


async def delete_business_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, _, biz_id = query.data.split(":")
    biz_id = int(biz_id)

    db = SessionLocal()
    try:
        biz = get_business(db, biz_id)
        if not biz or biz.owner_telegram_id != query.from_user.id:
            await query.answer("⛔ Not authorized.", show_alert=True)
            return
        delete_business(db, biz_id)
    finally:
        db.close()

    await query.edit_message_text("🗑️ Business deleted.")


async def details_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    biz_id = int(query.data.split(":")[1])
    user = query.from_user
    lang = _lang(user.id)

    db = SessionLocal()
    try:
        from db.queries import (
            get_business_rating, get_free_views_used,
            has_view_access, grant_view_access, has_pending_payment,
        )
        from config import FREE_VIEWS_QUOTA, VIEW_FEE, TELEBIRR_ACCOUNT, TELEBIRR_NAME

        biz = get_business(db, biz_id)
        if not biz:
            await query.answer("Business not found.", show_alert=True)
            return

        views_used = get_free_views_used(db, user.id)
        already_has_access = has_view_access(db, user.id, biz_id)

        # Grant free access if under quota
        if not already_has_access and views_used < FREE_VIEWS_QUOTA:
            grant_view_access(db, user.id, biz_id)
            already_has_access = True
            remaining = FREE_VIEWS_QUOTA - views_used - 1
            note = (
                f"ℹ️ Free view used. *{remaining}* free view{'s' if remaining != 1 else ''} remaining."
                if remaining > 0
                else "ℹ️ This was your last free view. Future details cost *3 ETB* via TeleBirr."
            )
            await query.message.reply_text(note, parse_mode="Markdown")

        if already_has_access:
            avg, count = get_business_rating(db, biz_id)
            from bot.formatters import format_business_detail
            text = format_business_detail(biz, avg, count, lang=lang)
            from bot.keyboards import business_card_keyboard
            kb = business_card_keyboard(
                biz.id, biz.phone, biz.telegram_username, biz.whatsapp,
                lat=biz.latitude, lon=biz.longitude,
            )
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=kb)
        else:
            # Check for already-pending payment
            if has_pending_payment(db, user.id, "view", biz_id):
                await query.message.reply_text(
                    "⏳ Your payment is pending admin approval. You'll be notified once approved."
                )
                return

            # Gate: ask for payment
            context.user_data["pay_type"] = "view"
            context.user_data["pay_ref_id"] = biz_id
            context.user_data["pay_biz_name"] = biz.name
            context.user_data["pay_amount"] = VIEW_FEE
            context.user_data["awaiting_view_payment"] = True

            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            await query.message.reply_text(
                f"🔒 *Full details require a small payment*\n\n"
                f"💰 Amount: *{VIEW_FEE} ETB*\n\n"
                f"📱 Send to:\n"
                f"👤 Name: *{TELEBIRR_NAME}*\n"
                f"📞 Number: `{TELEBIRR_ACCOUNT}`\n\n"
                f"_(Tap the number above to copy it)_\n\n"
                f"Then send a *screenshot* of the confirmation here.\n"
                f"Admin will approve and unlock *{biz.name}* for you.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Cancel", callback_data="pay:cancel_view")
                ]])
            )
    finally:
        db.close()


async def view_payment_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles screenshot sent by customer for a view payment."""
    if not context.user_data.get("awaiting_view_payment"):
        return

    photo = update.message.photo[-1] if update.message.photo else None
    doc = update.message.document
    file_id = photo.file_id if photo else (doc.file_id if doc else None)

    if not file_id:
        await update.message.reply_text("⚠️ Please send a *photo* screenshot of your TeleBirr payment.")
        return

    user = update.effective_user
    biz_id = context.user_data.get("pay_ref_id")
    biz_name = context.user_data.get("pay_biz_name", "")
    amount = context.user_data.get("pay_amount", 3)

    db = SessionLocal()
    try:
        from db.queries import create_payment_request, has_pending_payment
        if has_pending_payment(db, user.id, "view", biz_id):
            await update.message.reply_text("⏳ Already waiting for admin approval.")
            context.user_data.pop("awaiting_view_payment", None)
            return
        pr = create_payment_request(
            db, telegram_id=user.id, payment_type="view",
            reference_id=biz_id, amount=amount, screenshot_file_id=file_id,
        )
        pr_id = pr.id
    finally:
        db.close()

    await update.message.reply_text(
        "✅ Screenshot received! Admin will verify and unlock the details for you shortly."
    )

    from bot.handlers.payment import admin_payment_keyboard
    from config import ADMIN_IDS
    import logging
    logger = logging.getLogger(__name__)
    owner_tag = f"@{user.username}" if user.username else f"ID {user.id}"
    caption = (
        f"💳 *View Payment Screenshot*\n\n"
        f"👁️ Business: *{biz_name}*\n"
        f"👤 Customer: {owner_tag}\n"
        f"💰 Amount: {amount} ETB\n"
        f"🆔 Payment ID: #{pr_id}"
    )
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_photo(
                admin_id, photo=file_id,
                caption=caption, parse_mode="Markdown",
                reply_markup=admin_payment_keyboard(pr_id),
            )
        except Exception as e:
            logger.error("Failed to notify admin %s: %s", admin_id, e)

    context.user_data.pop("awaiting_view_payment", None)
    context.user_data.pop("pay_ref_id", None)
    context.user_data.pop("pay_biz_name", None)
    context.user_data.pop("pay_amount", None)


def get_mybusiness_conversation():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_field_start, pattern="^edit:(name|phone):")],
        states={
            EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_field_value)],
        },
        fallbacks=[],
        per_message=False,
    )


def get_handlers():
    return [
        CommandHandler("mybusiness", my_business),
    ]
