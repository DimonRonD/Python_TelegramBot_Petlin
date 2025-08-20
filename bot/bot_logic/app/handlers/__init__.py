from telegram.ext import BaseHandler, CommandHandler
from bot.bot_logic.app.handlers.commands import (
    start,
    help,
    add_event,
    list_events,
    del_event,
)

HANDLERS: tuple[BaseHandler] = (
    CommandHandler("start", start),
    CommandHandler("help", help),
    CommandHandler("add_event", add_event),
    CommandHandler("list_events", list_events),
    CommandHandler("del_event", del_event),
)
