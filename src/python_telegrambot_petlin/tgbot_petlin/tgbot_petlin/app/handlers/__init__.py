from telegram.ext import BaseHandler, CommandHandler
from src.python_telegrambot_petlin.tgbot_petlin.tgbot_petlin.app.handlers.commands import (start, help, add_note,
                                                                                           list_notes, del_note,
                                                                                           add_event, list_events,
                                                                                           del_event)

HANDLERS: tuple[BaseHandler] = (CommandHandler("start", start),
                                CommandHandler("help", help),
                                CommandHandler("add_note", add_note),
                                CommandHandler("list_notes", list_notes),
                                CommandHandler("del_note", del_note),
                                CommandHandler("add_event", add_event),
                                CommandHandler("list_events", list_events),
                                CommandHandler("del_events", del_event),
                                )


