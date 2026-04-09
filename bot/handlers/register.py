"""Business registration ConversationHandler with payment gate."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from db.models import SessionLocal
from db.queries import (
    get_or_create_user, create_business,
    owner_total_listing_count, has_pending_payment,
)
from bot.keyboards import (
    categories_keyboard, location_keyboard, cancel_keyboard,
    main_menu_keyboard, remove_keyboard, approve_business_keyboard,
)
from services.i18n import t
from config import ADMIN_IDS, FREE_LISTINGS_QUOTA, LISTING_FEE, TELEBIRR_ACCOUNT, TELEBIRR_NAME
import re

logger = logging.getLogger(__name__)

# States
NAME, CATEGORY, PHONE, LOCATION, DESCRIPTION, AWAIT_PAYMENT_SCREENSHOT = range(6)

PHONE_RE = re.compile(r"^\+?[\d\s\-]{7,20}$")


def _lang(telegram_id: int) -> str:
    db = SessionLocal()
    try:
        user = get_or_create_user(db, telegram_id, "")
        return user.language
    finally:
        db.close()


async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _lang(update.effective_user.id)
    context.user_data.clear()
    await update.message.reply_text(t("register_start", lang), reply_markup=cancel_keyboard())
    return NAME


async def got_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "❌ Cancel":
        return await _cancel(update, context)
    if len(text) < 2 or len(text) > 100:
        await update.message.reply_text("⚠️ Name must be 2–100 characters.")
        return NAME
    context.user_data["biz_name"] = text
    lang = _lang(update.effective_user.id)
    await update.message.reply_text(t("ask_category", lang), reply_markup=categories_keyboard("reg"))
    return CATEGORY


async def got_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, category = query.data.split(":", 1)
    context.user_data["biz_category"] = category
    lang = _lang(query.from_user.id)
    await query.edit_message_text(t("ask_phone", lang))
    return PHONE


async def got_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "❌ Cancel":
        return await _cancel(update, context)
    if not PHONE_RE.match(text):
        await update.message.reply_text("⚠️ Invalid phone number. Try again:")
        return PHONE
    context.user_data["biz_phone"] = text
    lang = _lang(update.effective_user.id)
    await update.message.reply_text(t("ask_location", lang), reply_markup=location_keyboard(lang))
    return LOCATION


async def got_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _lang(update.effective_user.id)
    if update.message.location:
        context.user_data["biz_lat"] = update.message.location.latitude
        context.user_data["biz_lon"] = update.message.location.longitude
        context.user_data["biz_area"] = None
    elif update.message.text == "✏️ Enter Area Manually":
        await update.message.reply_text("📝 Type your area name:", reply_markup=remove_keyboard())
        return LOCATION
    elif update.message.text == "❌ Cancel":
        return await _cancel(update, context)
    else:
        context.user_data["biz_area"] = update.message.text.strip()
        context.user_data["biz_lat"] = None
        context.user_data["biz_lon"] = None
    await update.message.reply_text(t("ask_description", lang), reply_markup=cancel_keyboard())
    return DESCRIPTION


async def got_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "❌ Cancel":
        return await _cancel(update, context)

    description = None if text == "/skip" else text
    lang = _lang(update.effective_user.id)
    user = update.effective_user

    db = SessionLocal()
    try:
        total = owner_total_listing_count(db, user.id)
        needs_payment = total >= FREE_LISTINGS_QUOTA

        # Save business as pending (not approved yet regardless)
        biz = create_business(
            db,
            name=context.user_data["biz_name"],
            category=context.user_data["biz_category"],
            phone=context.user_data["biz_phone"],
            latitude=context.user_data.get("biz_lat"),
            longitude=context.user_data.get("biz_lon"),
            area_name=context.user_data.get("biz_area"),
            description=description,
            owner_telegram_id=user.id,
            is_approved=False,
        )
        biz_id = biz.id
        biz_name = biz.name
    finally:
        db.close()

    if needs_payment:
        # Store for payment step
        context.user_data["pay_biz_id"] = biz_id
        context.user_data["pay_biz_name"] = biz_name

        await update.message.reply_text(
            f"🏪 Business *{biz_name}* saved!\n\n"
            f"💳 *Payment Required*\n\n"
            f"You've used your free listing. Each additional listing costs "
            f"*{LISTING_FEE} ETB* via TeleBirr.\n\n"
            f"📱 Send to:\n"
            f"👤 Name: *{TELEBIRR_NAME}*\n"
            f"📞 Number: `{TELEBIRR_ACCOUNT}`\n\n"
            f"_(Tap the number above to copy it)_\n\n"
            f"Then send a *screenshot* of the TeleBirr confirmation here.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel Listing", callback_data=f"reg:cancelpay:{biz_id}")
            ]])
        )
        return AWAIT_PAYMENT_SCREENSHOT
    else:
        # First free listing — notify admins directly
        await update.message.reply_text(t("registered_ok", lang), reply_markup=main_menu_keyboard(lang))
        await _notify_admins_new_listing(context, biz_id, biz_name, user)
        context.user_data.clear()
        return ConversationHandler.END


async def got_payment_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner sends TeleBirr screenshot for a paid listing."""
    photo = update.message.photo[-1] if update.message.photo else None
    doc = update.message.document
    file_id = photo.file_id if photo else (doc.file_id if doc else None)

    if not file_id:
        await update.message.reply_text("⚠️ Please send a *photo* of your TeleBirr confirmation.")
        return AWAIT_PAYMENT_SCREENSHOT

    user = update.effective_user
    biz_id = context.user_data.get("pay_biz_id")
    biz_name = context.user_data.get("pay_biz_name", "")
    lang = _lang(user.id)

    db = SessionLocal()
    try:
        if has_pending_payment(db, user.id, "listing", biz_id):
            await update.message.reply_text("⏳ Already waiting for admin approval on this listing.")
            return ConversationHandler.END

        from db.queries import create_payment_request
        pr = create_payment_request(
            db,
            telegram_id=user.id,
            payment_type="listing",
            reference_id=biz_id,
            amount=LISTING_FEE,
            screenshot_file_id=file_id,
        )
        pr_id = pr.id
    finally:
        db.close()

    await update.message.reply_text(
        "✅ Screenshot received! Admin will verify your payment.\n"
        "Your listing will go live once approved. 🎉",
        reply_markup=main_menu_keyboard(lang),
    )

    # Notify admins with screenshot + approve/reject
    owner_tag = f"@{user.username}" if user.username else f"ID {user.id}"
    caption = (
        f"💳 *Listing Payment Screenshot*\n\n"
        f"🏪 Business: *{biz_name}*\n"
        f"👤 Owner: {owner_tag}\n"
        f"💰 Amount: {LISTING_FEE} ETB\n"
        f"🆔 Payment ID: #{pr_id}"
    )
    from bot.handlers.payment import admin_payment_keyboard
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_photo(
                admin_id, photo=file_id,
                caption=caption, parse_mode="Markdown",
                reply_markup=admin_payment_keyboard(pr_id),
            )
        except Exception as e:
            logger.error("Failed to notify admin %s: %s", admin_id, e)

    context.user_data.clear()
    return ConversationHandler.END


async def cancel_listing_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner cancels a pending paid listing — delete the business record."""
    query = update.callback_query
    await query.answer()
    biz_id = int(query.data.split(":")[2])
    db = SessionLocal()
    try:
        from db.queries import delete_business
        delete_business(db, biz_id)
    finally:
        db.close()
    await query.edit_message_text("❌ Listing cancelled and removed.")
    context.user_data.clear()
    return ConversationHandler.END


async def _notify_admins_new_listing(context, biz_id, biz_name, user):
    owner_tag = f"@{user.username}" if user.username else f"ID {user.id}"
    msg = (
        f"🆕 *New Free Listing*\n\n"
        f"🏪 *{biz_name}*\n"
        f"👤 Owner: {owner_tag}"
    )
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id, msg, parse_mode="Markdown",
                reply_markup=approve_business_keyboard(biz_id),
            )
        except Exception as e:
            logger.error("Failed to notify admin %s: %s", admin_id, e)


async def _cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _lang(update.effective_user.id)
    context.user_data.clear()
    await update.message.reply_text(t("main_menu", lang), reply_markup=main_menu_keyboard(lang))
    return ConversationHandler.END


def get_register_conversation():
    return ConversationHandler(
        entry_points=[CommandHandler("register", register_start)],
        states={
            NAME:        [MessageHandler(filters.TEXT & ~filters.COMMAND, got_name)],
            CATEGORY:    [CallbackQueryHandler(got_category, pattern="^reg:")],
            PHONE:       [MessageHandler(filters.TEXT & ~filters.COMMAND, got_phone)],
            LOCATION:    [
                MessageHandler(filters.LOCATION, got_location),
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_location),
            ],
            DESCRIPTION: [
                MessageHandler(filters.TEXT, got_description),
                CommandHandler("skip", got_description),
            ],
            AWAIT_PAYMENT_SCREENSHOT: [
                MessageHandler(filters.PHOTO | filters.Document.IMAGE, got_payment_screenshot),
                CallbackQueryHandler(cancel_listing_payment, pattern="^reg:cancelpay:"),
            ],
        },
        fallbacks=[CommandHandler("cancel", _cancel)],
        per_message=False,
    )
