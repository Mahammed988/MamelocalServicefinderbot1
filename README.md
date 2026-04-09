# Local Service Finder Bot

A production-ready Telegram bot for discovering nearby local services and registering businesses.

## Features

- 🔍 Search by category or keyword
- 📍 Location-based results with distance (Haversine)
- ⭐ Featured listings always shown first
- 🏪 Business registration with admin approval flow
- 👤 Business owner dashboard (edit, toggle open/closed)
- ⭐ Ratings & reviews (1–5 stars)
- 🌐 Multi-language (English + Arabic)
- 📊 Admin analytics panel
- 📢 Admin broadcast messaging
- 🔒 Rate limiting & input validation

## Setup

### 1. Clone & install dependencies

```bash
cd local-service-finder-bot
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your BOT_TOKEN and ADMIN_IDS
```

Get your bot token from [@BotFather](https://t.me/BotFather).  
Get your Telegram user ID from [@userinfobot](https://t.me/userinfobot).

### 3. Initialize database & seed data

```bash
python seed.py
```

### 4. Run the bot

```bash
python main.py
```

## Database

- Default: SQLite (`bot.db`) — great for MVP/development
- Production: Set `DATABASE_URL=postgresql://user:pass@host:5432/dbname` in `.env`

## Commands

| Command | Description |
|---|---|
| `/start` | Welcome message + main menu |
| `/register` | Register a new business |
| `/mybusiness` | Manage your business listings |
| `/admin` | Admin panel (admin only) |
| `/language` | Switch language |
| `/help` | Help message |

## Admin Features

Access via `/admin` (your Telegram ID must be in `ADMIN_IDS`):
- Approve/reject new business registrations
- Mark businesses as featured
- View analytics (searches, top businesses, user count)
- Broadcast messages to all users

## Project Structure

```
local-service-finder-bot/
├── main.py                  # Entry point
├── config.py                # Settings & constants
├── seed.py                  # Example dataset (20 businesses)
├── requirements.txt
├── .env.example
├── db/
│   ├── models.py            # SQLAlchemy ORM models
│   └── queries.py           # All DB operations
├── services/
│   ├── location.py          # Haversine distance calculation
│   └── i18n.py              # English + Arabic translations
└── bot/
    ├── keyboards.py         # All inline & reply keyboards
    ├── formatters.py        # Business card formatting
    └── handlers/
        ├── start.py         # /start, /help, /language
        ├── search.py        # Search flow (ConversationHandler)
        ├── featured.py      # Featured services listing
        ├── register.py      # Business registration flow
        ├── mybusiness.py    # Owner dashboard
        ├── reviews.py       # Rating & review flow
        └── admin.py         # Admin panel
```

## Extending the Bot

The modular structure makes it easy to add:
- **Payments**: Add a `payments.py` handler + `payments` table
- **Maps**: Use `latitude/longitude` already stored to generate Google Maps links
- **AI recommendations**: Query `search_logs` + `reviews` to build a recommendation engine
- **More languages**: Add entries to `services/i18n.py`
