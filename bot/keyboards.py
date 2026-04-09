from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from config import CATEGORIES
from services.i18n import t


def main_menu_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["🔍 Find Service", "🏪 Categories"],
            ["⭐ Featured Services", "ℹ️ Help"],
        ],
        resize_keyboard=True,
    )


def categories_keyboard(prefix: str = "cat") -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(label, callback_data=f"{prefix}:{key}")]
        for key, label in CATEGORIES.items()
    ]
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back:main")])
    return InlineKeyboardMarkup(buttons)


def location_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📍 Share My Location", request_location=True)],
         ["✏️ Enter Area Manually"]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def business_card_keyboard(biz_id: int, phone: str = None,
                            telegram_username: str = None,
                            whatsapp: str = None,
                            lat: float = None,
                            lon: float = None) -> InlineKeyboardMarkup:
    buttons = []

    # Messaging buttons only — no tel: links (Telegram rejects many formats)
    row = []
    if telegram_username:
        row.append(InlineKeyboardButton("💬 Message", url=f"https://t.me/{telegram_username.lstrip('@')}"))
    if whatsapp:
        clean_wa = whatsapp.strip().replace(" ", "").replace("-", "").replace("+", "")
        row.append(InlineKeyboardButton("💬 WhatsApp", url=f"https://wa.me/{clean_wa}"))
    if row:
        buttons.append(row)

    # Map button if coordinates available
    if lat and lon:
        buttons.append([
            InlineKeyboardButton(
                "🗺️ View on Map",
                url=f"https://www.google.com/maps?q={lat},{lon}"
            )
        ])

    # Actions row
    buttons.append([
        InlineKeyboardButton("⭐ Rate", callback_data=f"rate:{biz_id}"),
        InlineKeyboardButton("ℹ️ Details", callback_data=f"details:{biz_id}"),
    ])
    return InlineKeyboardMarkup(buttons)


def see_results_keyboard(count: int) -> InlineKeyboardMarkup:
    """Summary button shown after search — user taps to load results."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📋 See {count} Result{'s' if count != 1 else ''}", callback_data="results:show:0")]
    ])


def rating_keyboard(biz_id: int) -> InlineKeyboardMarkup:
    stars = ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"]
    buttons = [
        [InlineKeyboardButton(stars[i], callback_data=f"rating:{biz_id}:{i+1}")]
        for i in range(5)
    ]
    buttons.append([InlineKeyboardButton("🔙 Cancel", callback_data=f"details:{biz_id}")])
    return InlineKeyboardMarkup(buttons)


def my_business_keyboard(biz_id: int, is_open: bool) -> InlineKeyboardMarkup:
    toggle_label = "🔴 Mark Closed" if is_open else "🟢 Mark Open"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Edit Name", callback_data=f"edit:name:{biz_id}"),
         InlineKeyboardButton("📞 Edit Phone", callback_data=f"edit:phone:{biz_id}")],
        [InlineKeyboardButton(toggle_label, callback_data=f"toggle:open:{biz_id}")],
        [InlineKeyboardButton("🗑️ Delete", callback_data=f"delete:biz:{biz_id}")],
    ])


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Pending Approvals", callback_data="admin:pending")],
        [InlineKeyboardButton("💳 Pending Payments", callback_data="admin:payments")],
        [InlineKeyboardButton("🏪 Manage Listings", callback_data="admin:listings")],
        [InlineKeyboardButton("👥 Manage Users", callback_data="admin:users")],
        [InlineKeyboardButton("📊 Analytics", callback_data="admin:analytics")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin:broadcast")],
        [InlineKeyboardButton("⭐ Manage Featured", callback_data="admin:featured")],
    ])


def approve_business_keyboard(biz_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"admin:approve:{biz_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"admin:reject:{biz_id}"),
            InlineKeyboardButton("⭐ Approve+Feature", callback_data=f"admin:feature:{biz_id}"),
        ]
    ])


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang:en"),
         InlineKeyboardButton("🇸🇦 العربية", callback_data="lang:ar")],
        [InlineKeyboardButton("🟢 Afaan Oromoo", callback_data="lang:or")],
    ])


def pagination_keyboard(page: int, total_pages: int, context_data: str) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    if page > 0:
        row.append(InlineKeyboardButton("◀️ Prev", callback_data=f"page:{page-1}:{context_data}"))
    if page < total_pages - 1:
        row.append(InlineKeyboardButton("Next ▶️", callback_data=f"page:{page+1}:{context_data}"))
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons) if buttons else None


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([["❌ Cancel"]], resize_keyboard=True, one_time_keyboard=True)


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
