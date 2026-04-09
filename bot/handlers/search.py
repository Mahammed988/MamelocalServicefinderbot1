"""Handles service search flow via ConversationHandler."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from db.models import SessionLocal
from db.queries import get_or_create_user, search_businesses, log_search
from bot.keyboards import (
    categories_keyboard, location_keyboard, business_card_keyboard,
    main_menu_keyboard, remove_keyboard, see_results_keyboard,
)
from bot.formatters import format_business_card
from services.i18n import t
from config import RESULTS_PER_PAGE

# States
CHOOSE_LOCATION, ENTER_AREA = range(2)

# bot_data key prefix — keyed per user so multiple users don't clash
def _rkey(user_id): return f"results_{user_id}"
def _lkey(user_id): return f"lang_{user_id}"


def _get_lang(telegram_id: int) -> str:
    db = SessionLocal()
    try:
        user = get_or_create_user(db, telegram_id, "")
        return user.language
    finally:
        db.close()


async def find_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _get_lang(update.effective_user.id)
    await update.message.reply_text(
        t("choose_category", lang),
        reply_markup=categories_keyboard("search"),
    )


async def categories_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _get_lang(update.effective_user.id)
    await update.message.reply_text(
        t("choose_category", lang),
        reply_markup=categories_keyboard("cat"),
    )


async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, category = query.data.split(":", 1)
    lang = _get_lang(query.from_user.id)

    context.user_data["search_category"] = category
    context.user_data["search_keyword"] = None

    await query.edit_message_text(t("share_location", lang))
    await query.message.reply_text(
        t("share_location", lang),
        reply_markup=location_keyboard(lang),
    )
    return CHOOSE_LOCATION


async def location_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _get_lang(update.effective_user.id)
    lat = lon = area = None

    if update.message.location:
        lat = update.message.location.latitude
        lon = update.message.location.longitude
    elif update.message.text == "✏️ Enter Area Manually":
        await update.message.reply_text("📝 Type your area name:", reply_markup=remove_keyboard())
        return ENTER_AREA
    else:
        area = update.message.text

    await _do_search(update, context, lat, lon, area, lang)
    return ConversationHandler.END


async def area_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _get_lang(update.effective_user.id)
    area = update.message.text.strip()
    await _do_search(update, context, None, None, area, lang)
    return ConversationHandler.END


async def _do_search(update, context, lat, lon, area, lang):
    category = context.user_data.get("search_category")
    keyword = context.user_data.get("search_keyword")
    user_id = update.effective_user.id

    await update.message.reply_text(t("searching", lang), reply_markup=remove_keyboard())

    db = SessionLocal()
    try:
        results = search_businesses(
            db, category=category, keyword=keyword, lat=lat, lon=lon, area=area
        )
        log_search(db, user_id, query=keyword, category=category,
                   area=area, results_count=len(results))
    finally:
        db.close()

    if not results:
        await update.message.reply_text(
            t("no_results", lang),
            reply_markup=main_menu_keyboard(lang),
        )
        return

    # Store in bot_data keyed by user_id — survives ConversationHandler.END
    context.bot_data[_rkey(user_id)] = results
    context.bot_data[_lkey(user_id)] = lang

    count = len(results)
    featured = sum(1 for r in results if r["business"]["is_featured"])

    lines = [f"🔍 Found *{count}* result{'s' if count != 1 else ''}"]
    if featured:
        lines.append(f"⭐ {featured} featured listing{'s' if featured != 1 else ''} on top")
    lines.append("\nTap below to browse:")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=see_results_keyboard(count),
    )


async def show_results_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fires when user taps 'See Results' or a pagination button."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    parts = query.data.split(":")       # results:show:<page>
    page = int(parts[2])

    # Load from bot_data — always available regardless of conversation state
    results = context.bot_data.get(_rkey(user_id), [])
    lang = context.bot_data.get(_lkey(user_id), "en")

    if not results:
        await query.edit_message_text("⚠️ Session expired. Please search again.")
        return

    total_pages = (len(results) + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE
    start = page * RESULTS_PER_PAGE
    page_results = results[start: start + RESULTS_PER_PAGE]

    # Remove the "See Results" button from the summary
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass

    for item in page_results:
        biz = item["business"]
        dist = item["distance"]
        text = format_business_card(biz, dist, lang)
        kb = business_card_keyboard(
            biz["id"],
            phone=biz["phone"],
            telegram_username=biz["telegram_username"],
            whatsapp=biz["whatsapp"],
            lat=biz["latitude"],
            lon=biz["longitude"],
        )
        await query.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)

    # Pagination footer
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(("◀️ Prev", f"results:show:{page - 1}"))
        if page < total_pages - 1:
            nav_buttons.append(("Next ▶️", f"results:show:{page + 1}"))
        if nav_buttons:
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton(label, callback_data=cb)
                for label, cb in nav_buttons
            ]])
            await query.message.reply_text(
                f"Page {page + 1} of {total_pages}",
                reply_markup=kb,
            )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _get_lang(update.effective_user.id)
    await update.message.reply_text(t("main_menu", lang), reply_markup=main_menu_keyboard(lang))
    return ConversationHandler.END


def get_search_conversation():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(category_selected, pattern="^(search|cat):"),
        ],
        states={
            CHOOSE_LOCATION: [
                MessageHandler(filters.LOCATION, location_received),
                MessageHandler(filters.TEXT & ~filters.COMMAND, location_received),
            ],
            ENTER_AREA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, area_entered),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )


def get_handlers():
    return [
        MessageHandler(filters.Regex("^🔍 Find Service$"), find_service),
        MessageHandler(filters.Regex("^🏪 Categories$"), categories_menu),
    ]
