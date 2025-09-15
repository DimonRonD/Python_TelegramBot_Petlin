from rest_framework import serializers
from .models import (
    TelegramUser,
    Event,
    Appointment,
    AppointmentUser,
    TempPassword,
    BotStatistic
)

class TelegramUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramUser
        fields = '__all__'

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'

class AppointmentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentUser
        fields = '__all__'

class TempPasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = TempPassword
        fields = '__all__'

class BotStatisticSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotStatistic
        fields = '__all__'