from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from db.models import SessionLocal
from db.queries import get_or_create_user, get_user
from bot.keyboards import main_menu_keyboard, language_keyboard
from services.i18n import t


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = SessionLocal()
    try:
        db_user = get_or_create_user(db, user.id, user.full_name, user.username)
        lang = db_user.language
    finally:
        db.close()

    await update.message.reply_text(
        t("welcome", lang),
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(lang),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = SessionLocal()
    try:
        db_user = get_or_create_user(db, user.id, user.full_name, user.username)
        lang = db_user.language
    finally:
        db.close()

    await update.message.reply_text(t("help_text", lang), parse_mode="Markdown")


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu from anywhere."""
    user = update.effective_user
    db = SessionLocal()
    try:
        db_user = get_or_create_user(db, user.id, user.full_name, user.username)
        lang = db_user.language
    finally:
        db.close()

    await update.message.reply_text(
        t("main_menu", lang),
        reply_markup=main_menu_keyboard(lang),
    )


async def whoami_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug: shows user's Telegram ID and whether they are admin."""
    from config import ADMIN_IDS
    user = update.effective_user
    is_admin = user.id in ADMIN_IDS
    await update.message.reply_text(
        f"🆔 Your Telegram ID: `{user.id}`\n"
        f"👤 Name: {user.full_name}\n"
        f"🔑 Admin: {'✅ Yes' if is_admin else '❌ No'}\n"
        f"📋 Admin IDs configured: `{ADMIN_IDS}`",
        parse_mode="Markdown",
    )


async def testnotify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin only: test that notifications reach all admin IDs."""
    from config import ADMIN_IDS
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Admin only.")
        return

    results = []
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                f"🔔 Test notification from `/testnotify`\nSent by: `{user.id}`",
                parse_mode="Markdown",
            )
            results.append(f"✅ {admin_id}")
        except Exception as e:
            results.append(f"❌ {admin_id}: {e}")

    await update.message.reply_text("\n".join(results))


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌐 Choose your language / اختر لغتك:",
        reply_markup=language_keyboard(),
    )


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split(":")[1]

    db = SessionLocal()
    try:
        from db.queries import set_user_language
        set_user_language(db, query.from_user.id, lang)
    finally:
        db.close()

    msg = "✅ Language set to English." if lang == "en" else ("✅ تم تعيين اللغة إلى العربية." if lang == "ar" else "✅ Afaan Oromoo filatame.")
    await query.edit_message_text(msg)


def get_handlers():
    return [
        CommandHandler("start", start),
        CommandHandler("help", help_command),
        CommandHandler("menu", menu_command),
        CommandHandler("whoami", whoami_command),
        CommandHandler("testnotify", testnotify_command),
        CommandHandler("language", language_command),
    ]
