from telegram.ext import BaseHandler, CommandHandler
from src.python_telegrambot_petlin.app.handlers.commands import start, help, add_note, list_notes, del_note
# from app.handlers.commands import start, help, add_note, list_notes, del_note

HANDLERS: tuple[BaseHandler] = (CommandHandler("start", start),
                                CommandHandler("help", help),
                                CommandHandler("add_note", add_note),
                                CommandHandler("list_notes", list_notes),
                                CommandHandler("del_note", del_note),
                                )


