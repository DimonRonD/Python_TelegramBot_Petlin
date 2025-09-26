FROM python:3.13
LABEL authors="dmitriipetlin"

WORKDIR /TGBot
COPY requirements.txt /TGBot

ENV PYTHONPATH = /TGBot

RUN pip install -r requirements.txt

COPY . /TGBot

RUN python manage.py makemigrations

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH = "${PYTHONPATH}:/TGBot"
ENV DJANGO_SETTINGS_MODULE=core.settings

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]