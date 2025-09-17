import json
import reverse
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseForbidden
from django.template import loader
from django.urls import reverse
from django.db.models import Q
from bot.forms import LoginForm, ExportForm

from rest_framework import viewsets
from .serializers import (
    TelegramUserSerializer,
    EventSerializer,
    AppointmentSerializer,
    AppointmentUserSerializer,
    TempPasswordSerializer,
    BotStatisticSerializer
)

from bot.models import TempPassword, AppointmentUser, Event, Appointment, TelegramUser, BotStatistic


# Create your views here.

def auth_site(request):
    template = loader.get_template('auth.html')
    context = {}
    form_password = ""
    rendered_page = template.render(context, request)

    if request.method == 'POST':
        form = LoginForm(request.POST)
        form_password = request.POST.get('password')

        try:
            temp_password = TempPassword.objects.get(password=form_password)
            tg_user = temp_password.tg


            redirect_url = reverse("calendar", args=(tg_user.user_id,))
            return HttpResponseRedirect(redirect_url)
        except Exception as e:
            return HttpResponse(f"Нихера не вышло {e}")

        # return redirect('calendar', 3)  # Redirect to a named URL pattern
    else:
        return HttpResponse(rendered_page)

def appointments(request, tg):
    user = TelegramUser.objects.get(user_id=tg)
    template = loader.get_template('appointments.html')
    user_appo = AppointmentUser.objects.select_related('appointment', 'telegram_user').filter(
        Q(telegram_user=tg) & (Q(status="Подтверждено") | Q(status="Ожидание")))
    publish_events = Event.objects.all().filter(Q(public=True))
    context = {"appointments": user_appo,
               "user": user.nick_name,
               "public_events": publish_events,}
    return render(request, 'appointments.html', context)


def export_json(request, tg):
    user = TelegramUser.objects.get(user_id=tg)
    #if request.method == 'GET':
    events = Event.objects.all().filter(Q(telegram_user=tg))

    print("We are in!")

    event_list = []
    for event in events:
        event_list.append({
            'id': event.event_id,
            'title': event.name,
            'date': event.date.strftime('%Y-%m-%d'),
            'time': event.time.strftime('%H-%m'),
            'public': event.public,

        })

    response = JsonResponse(event_list, safe=False, json_dumps_params={'ensure_ascii': False})
    response['Content-Disposition'] = 'attachment; filename=my_data.json'
    return response



class TelegramUserViewSet(viewsets.ModelViewSet):
    queryset = TelegramUser.objects.all()
    serializer_class = TelegramUserSerializer

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer

class AppointmentUserViewSet(viewsets.ModelViewSet):
    queryset = AppointmentUser.objects.all()
    serializer_class = AppointmentUserSerializer

class TempPasswordViewSet(viewsets.ModelViewSet):
    queryset = TempPassword.objects.all()
    serializer_class = TempPasswordSerializer

class BotStatisticViewSet(viewsets.ModelViewSet):
    queryset = BotStatistic.objects.all()
    serializer_class = BotStatisticSerializer