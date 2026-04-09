"""Rate limiting and spam prevention middleware."""
import time
from collections import defaultdict
from telegram import Update
from telegram.ext import ContextTypes

# Simple in-memory rate limiter: max N requests per window
RATE_LIMIT = 10       # max requests
RATE_WINDOW = 60      # per 60 seconds

_user_requests: dict = defaultdict(list)


async def rate_limit_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE, next_handler):
    if not update.effective_user:
        return await next_handler(update, context)

    user_id = update.effective_user.id
    now = time.time()
    window_start = now - RATE_WINDOW

    # Clean old entries
    _user_requests[user_id] = [t for t in _user_requests[user_id] if t > window_start]

    if len(_user_requests[user_id]) >= RATE_LIMIT:
        if update.message:
            await update.message.reply_text("⚠️ Too many requests. Please slow down.")
        return

    _user_requests[user_id].append(now)
    return await next_handler(update, context)
