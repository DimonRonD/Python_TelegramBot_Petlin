from telegram.ext import BaseHandler, CommandHandler
from bot.bot_logic.app.handlers.commands import (
    start,
    help,
    list_users,
    list_events,
    my_appo,
    add_event,
    del_event,
    confirm,
    reject,
    invite_user,
)

HANDLERS: tuple[BaseHandler] = (
    CommandHandler("start", start),
    CommandHandler("help", help),
    CommandHandler("list_users", list_users),
    CommandHandler("list_events", list_events),
    CommandHandler("my_appo", my_appo),
    CommandHandler("add_event", add_event),
    CommandHandler("del_event", del_event),
    CommandHandler("confirm", confirm),
    CommandHandler("reject", reject),
    CommandHandler("invite", invite_user),
)
