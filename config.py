import os
from dotenv import load_dotenv

load_dotenv()

# Bot
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
_admin_ids_raw = os.getenv("ADMIN_IDS", "6411140505,5892363411")
try:
    ADMIN_IDS = list(map(int, _admin_ids_raw.split(",")))
except ValueError:
    ADMIN_IDS = [6411140505, 5892363411]

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bot.db")

# Localization
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")

# Pagination
RESULTS_PER_PAGE = 5

# Payment
LISTING_FEE = 300          # ETB per listing after the free first one
VIEW_FEE = 3               # ETB per property detail view after 3 free views
FREE_VIEWS_QUOTA = 3       # how many free detail views a customer gets
FREE_LISTINGS_QUOTA = 1    # how many free listings an owner gets
TELEBIRR_ACCOUNT = "0983559506"   # TeleBirr number to pay to
TELEBIRR_NAME = "Mohammed"        # Account holder name

# Categories
CATEGORIES = {
    "mechanic": "🔧 Mechanic",
    "pharmacy": "💊 Pharmacy",
    "mobile_clinic": "🏥 Mobile Clinic",
    "supermarket": "🛒 Supermarket",
    "electronics": "📱 Electronics",
}

CATEGORY_EMOJIS = {
    "mechanic": "🔧",
    "pharmacy": "💊",
    "mobile_clinic": "🏥",
    "supermarket": "🛒",
    "electronics": "📱",
}
