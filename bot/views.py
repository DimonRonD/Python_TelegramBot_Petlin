from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
# Create your views here.


def auth_site(request):
    template = loader.get_template('auth.html')
    context = {}
    rendered_page = template.render(context, request)
    return HttpResponse(rendered_page)