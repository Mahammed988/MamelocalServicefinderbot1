"""Simple i18n support. Add more languages by extending STRINGS."""

STRINGS = {
    "en": {
        "welcome": (
            "👋 Welcome to *Local Service Finder Bot*!\n\n"
            "Find nearby services or register your business.\n"
            "Use the menu below to get started."
        ),
        "main_menu": "🏠 Main Menu",
        "choose_category": "📂 Choose a category:",
        "share_location": "📍 Please share your location or type your area name:",
        "searching": "🔍 Searching...",
        "no_results": "😕 No businesses found. Try a different area or category.",
        "results_header": "🔍 Found *{count}* result(s):",
        "register_start": "🏪 Let's register your business!\n\nWhat is your business name?",
        "ask_category": "📂 Select your business category:",
        "ask_phone": "📞 Enter your business phone number:",
        "ask_location": "📍 Share your business location or type the area name:",
        "ask_description": "📝 Add a short description (or type /skip):",
        "registered_ok": "✅ Business registered! Awaiting admin approval.",
        "no_business": "You have no registered businesses.",
        "help_text": (
            "ℹ️ *How to use this bot:*\n\n"
            "🔍 *Find Service* — Search by category or keyword\n"
            "🏪 *Categories* — Browse all service types\n"
            "⭐ *Featured* — See top promoted businesses\n"
            "/register — Register your business\n"
            "/mybusiness — Manage your listings\n"
            "/language — Change language\n\n"
            "Need help? Contact @support"
        ),
        "rate_prompt": "⭐ Rate this business (1–5):",
        "rate_saved": "✅ Review saved, thank you!",
        "open": "🟢 Open",
        "closed": "🔴 Closed",
        "featured_badge": "⭐ Featured",
        "admin_only": "⛔ Admin access only.",
        "broadcast_prompt": "📢 Enter the message to broadcast to all users:",
        "broadcast_sent": "✅ Broadcast sent to {count} users.",
        "language_select": "🌐 Choose your language:",
        "language_set": "✅ Language set to English.",
    },
    "ar": {
        "welcome": (
            "👋 مرحباً بك في *بوت البحث عن الخدمات المحلية*!\n\n"
            "ابحث عن الخدمات القريبة أو سجّل نشاطك التجاري.\n"
            "استخدم القائمة أدناه للبدء."
        ),
        "main_menu": "🏠 القائمة الرئيسية",
        "choose_category": "📂 اختر فئة:",
        "share_location": "📍 شارك موقعك أو اكتب اسم المنطقة:",
        "searching": "🔍 جاري البحث...",
        "no_results": "😕 لا توجد نتائج. جرّب منطقة أو فئة مختلفة.",
        "results_header": "🔍 تم العثور على *{count}* نتيجة:",
        "register_start": "🏪 لنسجّل نشاطك التجاري!\n\nما اسم نشاطك التجاري؟",
        "ask_category": "📂 اختر فئة نشاطك التجاري:",
        "ask_phone": "📞 أدخل رقم هاتف نشاطك التجاري:",
        "ask_location": "📍 شارك موقع نشاطك أو اكتب اسم المنطقة:",
        "ask_description": "📝 أضف وصفاً قصيراً (أو اكتب /skip):",
        "registered_ok": "✅ تم تسجيل النشاط التجاري! في انتظار موافقة المشرف.",
        "no_business": "ليس لديك أي نشاط تجاري مسجّل.",
        "help_text": (
            "ℹ️ *كيفية استخدام البوت:*\n\n"
            "🔍 *البحث عن خدمة* — ابحث حسب الفئة أو الكلمة المفتاحية\n"
            "🏪 *الفئات* — تصفح جميع أنواع الخدمات\n"
            "⭐ *المميزة* — شاهد أفضل الأنشطة التجارية\n"
            "/register — سجّل نشاطك التجاري\n"
            "/mybusiness — إدارة قوائمك\n"
            "/language — تغيير اللغة\n\n"
            "تحتاج مساعدة؟ تواصل مع @support"
        ),
        "rate_prompt": "⭐ قيّم هذا النشاط التجاري (1–5):",
        "rate_saved": "✅ تم حفظ تقييمك، شكراً!",
        "open": "🟢 مفتوح",
        "closed": "🔴 مغلق",
        "featured_badge": "⭐ مميز",
        "admin_only": "⛔ للمشرفين فقط.",
        "broadcast_prompt": "📢 أدخل الرسالة لإرسالها لجميع المستخدمين:",
        "broadcast_sent": "✅ تم الإرسال إلى {count} مستخدم.",
        "language_select": "🌐 اختر لغتك:",
        "language_set": "✅ تم تعيين اللغة إلى العربية.",
    },
    "or": {
        "welcome": (
            "👋 *Tajaajila Naannoo Barbaaduu Bot*-tti baga nagaan dhuftan!\n\n"
            "Tajaajila naannoo barbaadi ykn daldala kee galmeessi.\n"
            "Filannoowwan armaan gadii fayyadami."
        ),
        "main_menu": "🏠 Menuu Jalqabaa",
        "choose_category": "📂 Gosa filadhu:",
        "share_location": "📍 Bakka jirtu qoodaa ykn maqaa naannoo barreessi:",
        "searching": "🔍 Barbaadaa jira...",
        "no_results": "😕 Daldalli hin argamne. Naannoo ykn gosa biraa yaalii.",
        "results_header": "🔍 Bu'aa *{count}* argame:",
        "register_start": "🏪 Daldala kee galmeessina!\n\nMaqaan daldala kee maal?",
        "ask_category": "📂 Gosa daldala kee filadhu:",
        "ask_phone": "📞 Lakkoofsa bilbila daldala kee galchi:",
        "ask_location": "📍 Bakka daldala kee qoodaa ykn maqaa naannoo barreessi:",
        "ask_description": "📝 Ibsa gabaabaa ida'i (ykn /skip barreessi):",
        "registered_ok": "✅ Daldalli galmeeffame! Hayyama bulchiinsaa eegaa jira.",
        "no_business": "Daldala galmeeffame hin qabdu.",
        "help_text": (
            "ℹ️ *Bot kana akkamitti fayyadamuu:*\n\n"
            "🔍 *Tajaajila Barbaadi* — Gosa ykn keyword barbaadi\n"
            "🏪 *Gosawwan* — Gosawwan tajaajila hunda ilaali\n"
            "⭐ *Filatamoo* — Daldalawwan beekamoo ilaali\n"
            "/register — Daldala kee galmeessi\n"
            "/mybusiness — Galmeewwan kee bulchi\n"
            "/language — Afaan jijjiiri\n\n"
            "Gargaarsa barbaaddaa? @support qunnamaa"
        ),
        "rate_prompt": "⭐ Daldala kana madaali (1–5):",
        "rate_saved": "✅ Madaalliin kee kuufame, galatoomaa!",
        "open": "🟢 Banaa",
        "closed": "🔴 Cufaa",
        "featured_badge": "⭐ Filatamaa",
        "admin_only": "⛔ Bulchiinsa qofa.",
        "broadcast_prompt": "📢 Ergaa fayyadamtoota hundaaf erguu galchi:",
        "broadcast_sent": "✅ Ergaan fayyadamtoota {count} dhaqqabe.",
        "language_select": "🌐 Afaan kee filadhu:",
        "language_set": "✅ Afaan Oromoo filatame.",
    },
}


def t(key: str, lang: str = "en", **kwargs) -> str:
    """Translate a key to the given language."""
    text = STRINGS.get(lang, STRINGS["en"]).get(key, STRINGS["en"].get(key, key))
    if kwargs:
        text = text.format(**kwargs)
    return text
