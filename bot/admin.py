from django.contrib import admin

from bot.models import (
    Event,
    BotStatistic,
    Appointment,
    AppointmentUser,
    TelegramUser,
    TempPassword
)

# Register your models here.
admin.site.register(Event)

admin.site.register(BotStatistic)
admin.site.register(Appointment)
admin.site.register(AppointmentUser)
admin.site.register(TelegramUser)
admin.site.register(TempPassword)
