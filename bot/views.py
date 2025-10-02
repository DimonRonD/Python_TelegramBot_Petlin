import reverse
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseForbidden
from django.template import loader
from django.urls import reverse
from django.db.models import Q
from bot.forms import LoginForm
from django.core.cache import cache

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
            cache.set('telegram_id', f'{tg_user.tg_id}')
            temp_password.delete()

            redirect_url = reverse("calendar", args=(tg_user.user_id,))
            return HttpResponseRedirect(redirect_url)
        except Exception as e:
            return HttpResponse(f"Нихера не вышло {e}")
    else:
        return HttpResponse(rendered_page)

def appointments(request, tg):
    telegram_id = cache.get('telegram_id')
    user = TelegramUser.objects.get(user_id=tg)
    if telegram_id == user.tg_id:
        user_appo = AppointmentUser.objects.select_related('appointment', 'telegram_user').filter(
            Q(telegram_user=tg) & (Q(status="Подтверждено") | Q(status="Ожидание")))
        publish_events = Event.objects.all().filter(Q(public=True))
        context = {"appointments": user_appo,
                   "user": user.nick_name,
                   "public_events": publish_events,
                   "telegram_id": telegram_id,}
        return render(request, 'appointments.html', context)
    else:
        return HttpResponseForbidden("Вы пытаетесь зайти на страницу другого пользователя")


def export_json(request, tg):
    user = TelegramUser.objects.get(user_id=tg)
    events = Event.objects.all().filter(Q(telegram_user=tg))

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