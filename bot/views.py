import reverse
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseForbidden
from django.template import loader
from django.urls import reverse
from django.db.models import Q
from bot.forms import LoginForm, ExportForm

from bot.models import TempPassword, AppointmentUser, Event, Appointment, TelegramUser


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
    return JsonResponse({'events': event_list}, safe=False)
    # else:
    #     return JsonResponse({'error': 'Method not allowed'}, status=405)