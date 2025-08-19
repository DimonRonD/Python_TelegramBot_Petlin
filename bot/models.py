from django.contrib.auth.models import User
from django.db import models

class BaseModel(models.Model):
    objects = models.Manager

    class Meta:
        abstract = True

# Create your models here.
class Event(BaseModel):
    name = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()


class BotStatistic(BaseModel):
    date = models.DateField()
    user_count = models.PositiveIntegerField()
    event_count = models.PositiveIntegerField()
    edited_events = models.PositiveIntegerField()
    cancelled_events = models.PositiveIntegerField()


class Appointment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    details = models.TextField(blank=True)
    status = models.CharField(max_length=40)

    def __str__(self):
        return f"{self.user.username} - {self.event.name} - {self.date} - {self.time}"
