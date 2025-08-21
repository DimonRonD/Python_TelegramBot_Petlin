from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

class BaseModel(models.Model):
    objects = models.Manager

    class Meta:
        abstract = True

# Create your models here.
class Event(BaseModel):
    event_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()

    def __str__(self):
        return f'{self.event_id}, {self.name}, {self.date}, {self.time}'


class BotStatistic(BaseModel):
    date = models.DateField()
    user_count = models.PositiveIntegerField()
    event_count = models.PositiveIntegerField()
    edited_events = models.PositiveIntegerField()
    cancelled_events = models.PositiveIntegerField()


class TelegramUser(BaseModel):
    nick_name = models.CharField()
    tg_id = models.CharField()
    create_date = models.DateTimeField(auto_now_add=True)


class Appointment(BaseModel):
    appo_id = models.AutoField(primary_key=True)
    event = models.ForeignKey(Event, on_delete=models.PROTECT)
    date = models.DateField()
    time = models.TimeField()
    details = models.TextField(blank=True)
    status = models.CharField(max_length=40)


class AppointmentUser(BaseModel):
    appointment = models.ForeignKey(Appointment, on_delete=models.PROTECT, related_name='appointments')
    telegram_user = models.ForeignKey(TelegramUser, on_delete=models.PROTECT, related_name='telegram_users')
    status = models.CharField(max_length=40)

    def __str__(self):
        appointment = self.appointment
        event = appointment.event
        telegram_user = self.telegram_user

        return f"{appointment} - {telegram_user.nick_name} - {event.name} - {appointment.date} - {appointment.time} - {self.status}"


