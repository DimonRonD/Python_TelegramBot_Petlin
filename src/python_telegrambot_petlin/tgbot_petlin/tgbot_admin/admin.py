from django.contrib import admin

from src.python_telegrambot_petlin.tgbot_petlin.tgbot_admin.models import Event, BotStatistics

# Register your models here.
admin.site.register(Event)

admin.site.register(BotStatistics)