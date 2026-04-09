"""Admin panel — restricted to ADMIN_IDS."""
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from db.models import SessionLocal
from db.queries import (
    get_pending_businesses, get_business, update_business,
    delete_business, get_analytics, get_all_users
)
from bot.keyboards import admin_keyboard, approve_business_keyboard
from bot.formatters import format_business_card
from config import ADMIN_IDS
from services.i18n import t

# States
BROADCAST_MSG = range(1)


def is_admin(telegram_id: int) -> bool:
    return telegram_id in ADMIN_IDS


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin access only.")
        return

    await update.message.reply_text(
        "⚙️ *Admin Panel*\nChoose an action:",
        parse_mode="Markdown",
        reply_markup=admin_keyboard(),
    )


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer("⛔ Not authorized.", show_alert=True)
        return

    await query.answer()
    parts = query.data.split(":")
    action = parts[1]

    if action == "pending":
        await _show_pending(query)
    elif action == "analytics":
        await _show_analytics(query)
    elif action == "broadcast":
        await query.message.reply_text("📢 Enter broadcast message:")
        context.user_data["awaiting_broadcast"] = True
    elif action == "approve":
        biz_id = int(parts[2])
        await _approve(query, biz_id, featured=False)
    elif action == "feature":
        biz_id = int(parts[2])
        await _approve(query, biz_id, featured=True)
    elif action == "reject":
        biz_id = int(parts[2])
        await _reject(query, biz_id)
    elif action == "featured":
        await _manage_featured(query)


async def _show_pending(query):
    db = SessionLocal()
    try:
        pending = get_pending_businesses(db)
        if not pending:
            await query.edit_message_text("✅ No pending approvals.")
            return
        await query.edit_message_text(f"📋 *{len(pending)} pending businesses:*", parse_mode="Markdown")
        for biz in pending:
            text = format_business_card(biz)
            kb = approve_business_keyboard(biz.id)
            await query.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)
    finally:
        db.close()


async def _show_analytics(query):
    db = SessionLocal()
    try:
        stats = get_analytics(db)
        top = "\n".join(
            f"  {i+1}. {b.name} ({b.search_count} searches)"
            for i, b in enumerate(stats["top_businesses"])
        )
        text = (
            f"📊 *Analytics*\n\n"
            f"👥 Total Users: {stats['total_users']}\n"
            f"🏪 Total Businesses: {stats['total_businesses']}\n"
            f"🔍 Total Searches: {stats['total_searches']}\n\n"
            f"🏆 *Top Businesses:*\n{top or 'None yet'}"
        )
        await query.edit_message_text(text, parse_mode="Markdown")
    finally:
        db.close()


async def _approve(query, biz_id: int, featured: bool = False):
    db = SessionLocal()
    try:
        biz = update_business(db, biz_id, is_approved=True, is_featured=featured)
        if biz:
            label = "⭐ Approved & Featured" if featured else "✅ Approved"
            await query.edit_message_text(f"{label}: *{biz.name}*", parse_mode="Markdown")
            # Notify owner
            if biz.owner_telegram_id:
                try:
                    msg = f"✅ Your business *{biz.name}* has been approved!"
                    if featured:
                        msg += " It's also been marked as ⭐ Featured."
                    await query.get_bot().send_message(biz.owner_telegram_id, msg, parse_mode="Markdown")
                except Exception:
                    pass
    finally:
        db.close()


async def _reject(query, biz_id: int):
    db = SessionLocal()
    try:
        biz = get_business(db, biz_id)
        if biz:
            name = biz.name
            owner_id = biz.owner_telegram_id
            delete_business(db, biz_id)
            await query.edit_message_text(f"❌ Rejected & deleted: *{name}*", parse_mode="Markdown")
            if owner_id:
                try:
                    await query.get_bot().send_message(
                        owner_id,
                        f"❌ Your business *{name}* was not approved.",
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
    finally:
        db.close()


async def _manage_featured(query):
    db = SessionLocal()
    try:
        from db.models import Business
        businesses = db.query(Business).filter(Business.is_approved == True).all()
        if not businesses:
            await query.edit_message_text("No approved businesses.")
            return
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        buttons = []
        for biz in businesses:
            label = f"{'⭐ ' if biz.is_featured else ''}{biz.name}"
            toggle = "unfeature" if biz.is_featured else "setfeatured"
            buttons.append([InlineKeyboardButton(label, callback_data=f"feat:{toggle}:{biz.id}")])
        await query.edit_message_text("⭐ Toggle featured status:", reply_markup=InlineKeyboardMarkup(buttons))
    finally:
        db.close()


async def toggle_featured_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer("⛔ Not authorized.", show_alert=True)
        return
    await query.answer()
    _, action, biz_id = query.data.split(":")
    biz_id = int(biz_id)
    featured = action == "setfeatured"
    db = SessionLocal()
    try:
        update_business(db, biz_id, is_featured=featured)
    finally:
        db.close()
    label = "⭐ Marked as featured." if featured else "Removed from featured."
    await query.edit_message_text(label)


async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.user_data.get("awaiting_broadcast"):
        return

    context.user_data["awaiting_broadcast"] = False
    text = update.message.text
    db = SessionLocal()
    try:
        users = get_all_users(db)
    finally:
        db.close()

    sent = 0
    for user in users:
        try:
            await context.bot.send_message(user.telegram_id, f"📢 *Announcement*\n\n{text}", parse_mode="Markdown")
            sent += 1
        except Exception:
            pass

    await update.message.reply_text(f"✅ Broadcast sent to {sent} users.")


def get_handlers():
    return [
        CommandHandler("admin", admin_panel),
    ]
