"""Local Service Finder Bot — entry point."""
import logging
from telegram.ext import (
    Application, CallbackQueryHandler, MessageHandler, filters
)
from config import BOT_TOKEN, ADMIN_IDS
from db.models import init_db

# Handlers
from bot.handlers.start import get_handlers as start_handlers, language_callback, menu_command
from bot.handlers.search import get_handlers as search_handlers, get_search_conversation, show_results_callback
from bot.handlers.featured import get_handlers as featured_handlers
from bot.handlers.register import get_register_conversation
from bot.handlers.mybusiness import (
    get_handlers as mybusiness_handlers,
    get_mybusiness_conversation,
    toggle_open, delete_business_callback, details_callback,
    view_payment_screenshot,
)
from bot.handlers.reviews import get_review_conversation, rate_start
from bot.handlers.admin import (
    get_handlers as admin_handlers,
    admin_callback, toggle_featured_callback,
    broadcast_message,
)
from bot.handlers.payment import admin_payment_callback

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    init_db()
    logger.info("Database initialized.")
    logger.info("Admin IDs loaded: %s", ADMIN_IDS)
    logger.info("Bot token set: %s", "YES" if BOT_TOKEN else "NO - BOT_TOKEN missing!")

    # Auto-seed if database is empty (first deploy on Railway/fresh PostgreSQL)
    from db.models import SessionLocal
    from db.models import Business
    db = SessionLocal()
    try:
        count = db.query(Business).count()
        if count == 0:
            logger.info("Empty database detected — running seed...")
            from seed import seed
            seed()
            logger.info("Seed complete.")
    except Exception as e:
        logger.warning("Seed check failed: %s", e)
    finally:
        db.close()

    # Register bot commands — shows in Telegram's menu button (bottom-left)
    from telegram import BotCommand
    commands = [
        BotCommand("start",      "🏠 Main menu"),
        BotCommand("menu",       "🏠 Back to main menu"),
        BotCommand("register",   "🏪 Register your business"),
        BotCommand("mybusiness", "📋 Manage your listings"),
        BotCommand("language",   "🌐 Change language"),
        BotCommand("help",       "ℹ️ Help"),
        BotCommand("cancel",     "❌ Cancel current action"),
    ]

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(lambda application: application.bot.set_my_commands(commands))
        .build()
    )

    # Conversations (registered before generic handlers)
    app.add_handler(get_register_conversation())
    app.add_handler(get_search_conversation())
    app.add_handler(get_mybusiness_conversation())
    app.add_handler(get_review_conversation())

    # Command & message handlers
    for handler in start_handlers():
        app.add_handler(handler)
    for handler in search_handlers():
        app.add_handler(handler)
    for handler in featured_handlers():
        app.add_handler(handler)
    for handler in mybusiness_handlers():
        app.add_handler(handler)
    for handler in admin_handlers():
        app.add_handler(handler)

    # Callback query handlers
    app.add_handler(CallbackQueryHandler(language_callback, pattern="^lang:"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin:"))
    app.add_handler(CallbackQueryHandler(admin_payment_callback, pattern="^pay:(approve|reject):"))
    app.add_handler(CallbackQueryHandler(toggle_featured_callback, pattern="^feat:"))
    app.add_handler(CallbackQueryHandler(toggle_open, pattern="^toggle:open:"))
    app.add_handler(CallbackQueryHandler(delete_business_callback, pattern="^delete:biz:"))
    app.add_handler(CallbackQueryHandler(details_callback, pattern="^details:"))
    app.add_handler(CallbackQueryHandler(rate_start, pattern="^rate:"))
    app.add_handler(CallbackQueryHandler(show_results_callback, pattern="^results:show:"))

    # View payment screenshot — fires when customer sends photo after being gated
    app.add_handler(
        MessageHandler(
            filters.PHOTO & ~filters.COMMAND,
            view_payment_screenshot,
        )
    )

    # Help & Menu buttons
    from bot.handlers.start import help_command
    app.add_handler(MessageHandler(filters.Regex("^ℹ️ Help$"), help_command))
    app.add_handler(MessageHandler(filters.Regex("^🏠 Menu$"), menu_command))

    # Admin broadcast (last — only fires when admin has broadcast mode active)
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_IDS),
            broadcast_message,
        )
    )

    logger.info("Bot started. Polling...")

    async def error_handler(update, context):
        logger.error("Unhandled exception: %s", context.error, exc_info=context.error)
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text("⚠️ An error occurred. Please try again.")
            except Exception:
                pass

    app.add_error_handler(error_handler)
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
