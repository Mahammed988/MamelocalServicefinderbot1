"""
Payment flow for both owners (listing fee) and customers (view fee).

Owner flow:
  /register → free if first listing → else ask for 300 ETB TeleBirr screenshot
  → admin approves payment → listing goes live

Customer flow:
  tap Details on a business → free if under quota → else ask for 3 ETB screenshot
  → admin approves → customer unlocks that specific business details
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler,
    CallbackQueryHandler, filters
)
from db.models import SessionLocal
from db.queries import (
    get_or_create_user, create_payment_request, has_pending_payment,
    get_free_views_used, has_view_access, get_business,
)
from bot.keyboards import main_menu_keyboard
from config import LISTING_FEE, VIEW_FEE, FREE_VIEWS_QUOTA, TELEBIRR_ACCOUNT, TELEBIRR_NAME, ADMIN_IDS

logger = logging.getLogger(__name__)

# ConversationHandler state
AWAIT_SCREENSHOT = 0


# ── Helpers ────────────────────────────────────────────────────────────────

def payment_instruction(amount: int, reason: str) -> str:
    return (
        f"💳 *TeleBirr Payment Required*\n\n"
        f"📌 Reason: {reason}\n"
        f"💰 Amount: *{amount} ETB*\n\n"
        f"📱 Send to:\n"
        f"👤 Name: *{TELEBIRR_NAME}*\n"
        f"📞 Number: `{TELEBIRR_ACCOUNT}`\n\n"
        f"_(Tap the number above to copy it)_\n\n"
        f"After paying, send a *screenshot* of the confirmation here.\n"
        f"Admin will verify and approve within minutes."
    )


def admin_payment_keyboard(pr_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Approve Payment", callback_data=f"pay:approve:{pr_id}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"pay:reject:{pr_id}"),
    ]])


# ── Owner listing payment ──────────────────────────────────────────────────

async def request_listing_payment(update_or_message, context: ContextTypes.DEFAULT_TYPE,
                                   business_id: int, business_name: str):
    """Called from register.py when owner needs to pay for a listing."""
    context.user_data["pay_type"] = "listing"
    context.user_data["pay_ref_id"] = business_id
    context.user_data["pay_amount"] = LISTING_FEE

    msg = payment_instruction(LISTING_FEE, f"Listing: *{business_name}*")
    if hasattr(update_or_message, "message"):
        await update_or_message.message.reply_text(
            msg, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="pay:cancel")
            ]])
        )
    else:
        await update_or_message.reply_text(msg, parse_mode="Markdown")
    return AWAIT_SCREENSHOT


# ── Customer view payment ──────────────────────────────────────────────────

async def request_view_payment(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                business_id: int, business_name: str):
    """Called from details callback when customer needs to pay to view."""
    context.user_data["pay_type"] = "view"
    context.user_data["pay_ref_id"] = business_id
    context.user_data["pay_amount"] = VIEW_FEE

    msg = payment_instruction(VIEW_FEE, f"View details: *{business_name}*")
    await update.callback_query.message.reply_text(
        msg, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data="pay:cancel")
        ]])
    )
    return AWAIT_SCREENSHOT


# ── Screenshot received ────────────────────────────────────────────────────

async def screenshot_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User sends a photo as payment proof."""
    user = update.effective_user
    pay_type = context.user_data.get("pay_type")
    ref_id = context.user_data.get("pay_ref_id")
    amount = context.user_data.get("pay_amount")

    if not pay_type or not ref_id:
        await update.message.reply_text("⚠️ Session expired. Please start again.")
        return ConversationHandler.END

    # Get file_id of the photo
    photo = update.message.photo[-1] if update.message.photo else None
    doc = update.message.document
    file_id = photo.file_id if photo else (doc.file_id if doc else None)

    if not file_id:
        await update.message.reply_text("⚠️ Please send a photo screenshot.")
        return AWAIT_SCREENSHOT

    db = SessionLocal()
    try:
        # Check for duplicate pending
        if has_pending_payment(db, user.id, pay_type, ref_id):
            await update.message.reply_text(
                "⏳ You already have a pending payment for this. Please wait for admin approval."
            )
            return ConversationHandler.END

        pr = create_payment_request(
            db,
            telegram_id=user.id,
            payment_type=pay_type,
            reference_id=ref_id,
            amount=amount,
            screenshot_file_id=file_id,
        )
        pr_id = pr.id

        biz = get_business(db, ref_id)
        biz_name = biz.name if biz else f"ID {ref_id}"
    finally:
        db.close()

    await update.message.reply_text(
        "✅ Screenshot received! Admin will verify your payment shortly.\n"
        "You'll get a notification once approved."
    )

    # Notify admins
    owner_tag = f"@{user.username}" if user.username else f"ID {user.id}"
    type_label = "📋 Listing Fee" if pay_type == "listing" else "👁️ View Fee"
    caption = (
        f"💳 *New Payment Screenshot*\n\n"
        f"{type_label}\n"
        f"👤 From: {owner_tag}\n"
        f"🏪 Business: *{biz_name}*\n"
        f"💰 Amount: {amount} ETB\n"
        f"🆔 Payment ID: #{pr_id}"
    )
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_photo(
                admin_id,
                photo=file_id,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=admin_payment_keyboard(pr_id),
            )
        except Exception as e:
            logger.error("Failed to notify admin %s about payment: %s", admin_id, e)

    context.user_data.pop("pay_type", None)
    context.user_data.pop("pay_ref_id", None)
    context.user_data.pop("pay_amount", None)
    return ConversationHandler.END


async def pay_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Payment cancelled.")
    context.user_data.pop("pay_type", None)
    context.user_data.pop("pay_ref_id", None)
    context.user_data.pop("pay_amount", None)
    return ConversationHandler.END


# ── Admin payment approval callback ───────────────────────────────────────

async def admin_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles pay:approve:<id> and pay:reject:<id> from admin."""
    query = update.callback_query
    await query.answer()

    from config import ADMIN_IDS
    if query.from_user.id not in ADMIN_IDS:
        await query.answer("⛔ Not authorized.", show_alert=True)
        return

    parts = query.data.split(":")   # pay:approve:123
    action = parts[1]
    pr_id = int(parts[2])

    db = SessionLocal()
    try:
        from db.queries import approve_payment, reject_payment, get_payment_request
        from db.queries import grant_view_access, update_business

        pr = get_payment_request(db, pr_id)
        if not pr:
            await query.edit_message_caption("⚠️ Payment record not found.")
            return

        if action == "approve":
            approve_payment(db, pr_id)

            if pr.payment_type == "listing":
                # Approve the business listing
                update_business(db, pr.reference_id, is_approved=True)
                user_msg = (
                    f"✅ Your payment of {pr.amount} ETB has been approved!\n"
                    f"Your listing is now live. 🎉"
                )
            else:
                # Grant view access to this customer
                grant_view_access(db, pr.telegram_id, pr.reference_id)
                biz = get_business(db, pr.reference_id)
                user_msg = (
                    f"✅ Payment approved! You can now view the full details of "
                    f"*{biz.name if biz else 'the business'}*.\n"
                    f"Tap ℹ️ Details on the listing to see it."
                )

            await query.edit_message_caption(
                query.message.caption + "\n\n✅ *Approved*",
                parse_mode="Markdown",
            )
            try:
                await context.bot.send_message(
                    pr.telegram_id, user_msg, parse_mode="Markdown"
                )
            except Exception as e:
                logger.error("Could not notify user %s: %s", pr.telegram_id, e)

        elif action == "reject":
            reject_payment(db, pr_id)

            # If listing payment rejected, delete the pending business too
            if pr.payment_type == "listing":
                from db.queries import delete_business
                delete_business(db, pr.reference_id)

            await query.edit_message_caption(
                query.message.caption + "\n\n❌ *Rejected*",
                parse_mode="Markdown",
            )
            try:
                await context.bot.send_message(
                    pr.telegram_id,
                    f"❌ Your payment of {pr.amount} ETB was not verified. "
                    f"Please try again with a valid screenshot."
                )
            except Exception as e:
                logger.error("Could not notify user %s: %s", pr.telegram_id, e)
    finally:
        db.close()


def get_payment_conversation():
    return ConversationHandler(
        entry_points=[],   # triggered programmatically, not by command
        states={
            AWAIT_SCREENSHOT: [
                MessageHandler(filters.PHOTO | filters.Document.IMAGE, screenshot_received),
            ],
        },
        fallbacks=[CallbackQueryHandler(pay_cancel, pattern="^pay:cancel$")],
        per_message=False,
        name="payment_conv",
    )
