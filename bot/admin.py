from django.contrib import admin

from bot.models import (
    Event,
    BotStatistic,
)

# Register your models here.
admin.site.register(Event)

admin.site.register(BotStatistic)
