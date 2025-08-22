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


class TelegramUser(BaseModel):
    user_id = models.AutoField(primary_key=True)
    nick_name = models.CharField()
    tg_id = models.CharField()
    create_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        user_id = self.user_id
        nick_name = self.nick_name
        tg_id = self.tg_id
        return f"{user_id} - {nick_name} - {tg_id}"

class Appointment(BaseModel):
    appo_id = models.AutoField(primary_key=True)
    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name='event')
    date = models.DateField()
    time = models.TimeField()
    details = models.TextField(blank=True)
    status = models.CharField(max_length=40)

    def __str__(self):
        appo_id = self.appo_id
        event = self.event
        date = self.date
        time = self.time
        details = self.details
        status = self.status

        return f"{appo_id}  - {event} - {details} - {date} - {time} - {status}"


class AppointmentUser(BaseModel):
    appointment = models.ForeignKey(Appointment, on_delete=models.PROTECT, related_name='appointments')
    telegram_user = models.ForeignKey(TelegramUser, on_delete=models.PROTECT, related_name='telegram_users')
    status = models.CharField(max_length=40)

    def __str__(self):
        appointment = self.appointment
        event = appointment.event
        telegram_user = self.telegram_user

        return f"{appointment.appo_id} - {telegram_user.nick_name} - {event.name} - {appointment.date} - {appointment.time} - {self.status}"


class TempPassword(BaseModel):
    tg = models.OneToOneField(TelegramUser, on_delete=models.PROTECT, primary_key=True)
    password = models.CharField(max_length=10)

    def __str__(self):
        return f'{self.password}'

class BotStatistic(BaseModel):
    date = models.DateField()
    user_count = models.PositiveIntegerField()
    event_count = models.PositiveIntegerField()
    edited_events = models.PositiveIntegerField()
    cancelled_events = models.PositiveIntegerField()
    tg_id = models.ForeignKey(TelegramUser, on_delete=models.PROTECT, related_name='telegram_user')

