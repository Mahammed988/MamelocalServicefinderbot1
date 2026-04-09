"""Admin panel — restricted to ADMIN_IDS."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from db.models import SessionLocal
from db.queries import (
    get_pending_businesses, get_business, update_business,
    delete_business, get_analytics, get_all_users, get_user,
    get_pending_payments, get_payment_request,
    approve_payment, reject_payment,
)
from bot.keyboards import admin_keyboard, approve_business_keyboard
from bot.formatters import format_business_card
from config import ADMIN_IDS

logger = logging.getLogger(__name__)


def is_admin(telegram_id: int) -> bool:
    return telegram_id in ADMIN_IDS


def _auth(query):
    if not is_admin(query.from_user.id):
        return False
    return True


# ── Panel entry ────────────────────────────────────────────────────────────

async def admin_panel(update: Update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin access only.")
        return
    await update.message.reply_text(
        "⚙️ *Admin Panel*\nChoose an action:",
        parse_mode="Markdown",
        reply_markup=admin_keyboard(),
    )


# ── Main callback router ───────────────────────────────────────────────────

async def admin_callback(update: Update, context):
    query = update.callback_query
    if not _auth(query):
        await query.answer("⛔ Not authorized.", show_alert=True)
        return
    await query.answer()
    parts = query.data.split(":")
    action = parts[1]

    if action == "pending":
        await _show_pending(query)
    elif action == "payments":
        await _show_pending_payments(query)
    elif action == "listings":
        await _show_all_listings(query, context)
    elif action == "users":
        await _show_all_users(query, context)
    elif action == "analytics":
        await _show_analytics(query)
    elif action == "broadcast":
        await query.message.reply_text("📢 Enter broadcast message:")
        context.user_data["awaiting_broadcast"] = True
    elif action == "approve":
        await _approve(query, int(parts[2]), featured=False)
    elif action == "feature":
        await _approve(query, int(parts[2]), featured=True)
    elif action == "reject":
        await _reject_listing(query, int(parts[2]))
    elif action == "unapprove":
        await _unapprove_listing(query, int(parts[2]))
    elif action == "delbiz":
        await _delete_listing(query, int(parts[2]))
    elif action == "deluser":
        await _delete_user(query, int(parts[2]))
    elif action == "featured":
        await _manage_featured(query)
    elif action == "listpage":
        await _show_all_listings(query, context, page=int(parts[2]))
    elif action == "userpage":
        await _show_all_users(query, context, page=int(parts[2]))


# ── Pending listing approvals ──────────────────────────────────────────────

async def _show_pending(query):
    db = SessionLocal()
    try:
        pending = get_pending_businesses(db)
        if not pending:
            await query.edit_message_text("✅ No pending approvals.")
            return
        await query.edit_message_text(
            f"📋 *{len(pending)} pending businesses:*", parse_mode="Markdown"
        )
        for biz in pending:
            text = format_business_card(biz)
            kb = approve_business_keyboard(biz.id)
            await query.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)
    finally:
        db.close()


# ── Pending payments ───────────────────────────────────────────────────────

async def _show_pending_payments(query):
    db = SessionLocal()
    try:
        payments = get_pending_payments(db)
        if not payments:
            await query.edit_message_text("✅ No pending payments.")
            return
        await query.edit_message_text(
            f"💳 *{len(payments)} pending payment(s):*", parse_mode="Markdown"
        )
        for pr in payments:
            biz = get_business(db, pr.reference_id)
            biz_name = biz.name if biz else f"ID {pr.reference_id}"
            type_label = "📋 Listing Fee" if pr.payment_type == "listing" else "👁️ View Fee"
            text = (
                f"💳 *Payment #{pr.id}*\n"
                f"{type_label}\n"
                f"🏪 {biz_name}\n"
                f"👤 User ID: `{pr.telegram_id}`\n"
                f"💰 {pr.amount} ETB"
            )
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Approve", callback_data=f"pay:approve:{pr.id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"pay:reject:{pr.id}"),
            ]])
            if pr.screenshot_file_id:
                try:
                    await query.message.reply_photo(
                        pr.screenshot_file_id, caption=text,
                        parse_mode="Markdown", reply_markup=kb
                    )
                    continue
                except Exception:
                    pass
            await query.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)
    finally:
        db.close()


# ── Manage all listings ────────────────────────────────────────────────────

async def _show_all_listings(query, context, page: int = 0):
    PAGE = 8
    db = SessionLocal()
    try:
        from db.models import Business
        all_biz = db.query(Business).order_by(Business.created_at.desc()).all()
        total = len(all_biz)
        chunk = all_biz[page * PAGE: (page + 1) * PAGE]

        lines = [f"🏪 *All Listings* ({total} total) — Page {page+1}\n"]
        buttons = []
        for biz in chunk:
            status = "✅" if biz.is_approved else "⏳"
            feat = "⭐" if biz.is_featured else ""
            lines.append(f"{status}{feat} {biz.name} ({biz.category})")
            row = [
                InlineKeyboardButton(
                    f"🗑️ {biz.name[:15]}", callback_data=f"admin:delbiz:{biz.id}"
                ),
            ]
            if biz.is_approved:
                row.append(InlineKeyboardButton("🔄 Unapprove", callback_data=f"admin:unapprove:{biz.id}"))
            buttons.append(row)

        # Pagination
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"admin:listpage:{page-1}"))
        if (page + 1) * PAGE < total:
            nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"admin:listpage:{page+1}"))
        if nav:
            buttons.append(nav)

        await query.edit_message_text(
            "\n".join(lines), parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
        )
    finally:
        db.close()


# ── Manage users ───────────────────────────────────────────────────────────

async def _show_all_users(query, context, page: int = 0):
    PAGE = 8
    db = SessionLocal()
    try:
        users = get_all_users(db)
        total = len(users)
        chunk = users[page * PAGE: (page + 1) * PAGE]

        lines = [f"👥 *All Users* ({total} total) — Page {page+1}\n"]
        buttons = []
        for u in chunk:
            tag = f"@{u.username}" if u.username else f"ID {u.telegram_id}"
            lines.append(f"• {u.name} ({tag})")
            buttons.append([
                InlineKeyboardButton(
                    f"🗑️ {u.name[:15]}", callback_data=f"admin:deluser:{u.id}"
                )
            ])

        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"admin:userpage:{page-1}"))
        if (page + 1) * PAGE < total:
            nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"admin:userpage:{page+1}"))
        if nav:
            buttons.append(nav)

        await query.edit_message_text(
            "\n".join(lines), parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
        )
    finally:
        db.close()


# ── Listing actions ────────────────────────────────────────────────────────

async def _approve(query, biz_id: int, featured: bool = False):
    db = SessionLocal()
    try:
        biz = update_business(db, biz_id, is_approved=True, is_featured=featured)
        if biz:
            label = "⭐ Approved & Featured" if featured else "✅ Approved"
            await query.edit_message_text(f"{label}: *{biz.name}*", parse_mode="Markdown")
            if biz.owner_telegram_id:
                try:
                    msg = f"✅ Your business *{biz.name}* has been approved!"
                    if featured:
                        msg += " It's also been marked as ⭐ Featured."
                    await query.get_bot().send_message(
                        biz.owner_telegram_id, msg, parse_mode="Markdown"
                    )
                except Exception:
                    pass
    finally:
        db.close()


async def _reject_listing(query, biz_id: int):
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


async def _unapprove_listing(query, biz_id: int):
    db = SessionLocal()
    try:
        biz = update_business(db, biz_id, is_approved=False, is_featured=False)
        if biz:
            await query.edit_message_text(
                f"🔄 *{biz.name}* unapproved — hidden from search.",
                parse_mode="Markdown"
            )
            if biz.owner_telegram_id:
                try:
                    await query.get_bot().send_message(
                        biz.owner_telegram_id,
                        f"⚠️ Your listing *{biz.name}* has been suspended by admin.",
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
    finally:
        db.close()


async def _delete_listing(query, biz_id: int):
    db = SessionLocal()
    try:
        biz = get_business(db, biz_id)
        if biz:
            name = biz.name
            owner_id = biz.owner_telegram_id
            delete_business(db, biz_id)
            await query.edit_message_text(f"🗑️ Deleted: *{name}*", parse_mode="Markdown")
            if owner_id:
                try:
                    await query.get_bot().send_message(
                        owner_id,
                        f"🗑️ Your listing *{name}* has been deleted by admin.",
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
    finally:
        db.close()


async def _delete_user(query, user_db_id: int):
    db = SessionLocal()
    try:
        from db.models import User
        user = db.query(User).filter(User.id == user_db_id).first()
        if user:
            name = user.name
            db.delete(user)
            db.commit()
            await query.edit_message_text(f"🗑️ User *{name}* deleted.", parse_mode="Markdown")
    finally:
        db.close()


# ── Analytics ──────────────────────────────────────────────────────────────

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


# ── Featured management ────────────────────────────────────────────────────

async def _manage_featured(query):
    db = SessionLocal()
    try:
        from db.models import Business
        businesses = db.query(Business).filter(Business.is_approved == True).all()
        if not businesses:
            await query.edit_message_text("No approved businesses.")
            return
        buttons = []
        for biz in businesses:
            label = f"{'⭐ ' if biz.is_featured else ''}{biz.name}"
            toggle = "unfeature" if biz.is_featured else "setfeatured"
            buttons.append([InlineKeyboardButton(label, callback_data=f"feat:{toggle}:{biz.id}")])
        await query.edit_message_text(
            "⭐ Toggle featured status:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    finally:
        db.close()


async def toggle_featured_callback(update: Update, context):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer("⛔ Not authorized.", show_alert=True)
        return
    await query.answer()
    _, action, biz_id = query.data.split(":")
    featured = action == "setfeatured"
    db = SessionLocal()
    try:
        update_business(db, int(biz_id), is_featured=featured)
    finally:
        db.close()
    await query.edit_message_text("⭐ Marked as featured." if featured else "Removed from featured.")


# ── Broadcast ──────────────────────────────────────────────────────────────

async def broadcast_message(update: Update, context):
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
            await context.bot.send_message(
                user.telegram_id, f"📢 *Announcement*\n\n{text}", parse_mode="Markdown"
            )
            sent += 1
        except Exception:
            pass
    await update.message.reply_text(f"✅ Broadcast sent to {sent} users.")


def get_handlers():
    return [CommandHandler("admin", admin_panel)]
