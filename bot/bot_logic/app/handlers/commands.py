import re
import random
import string
from collections import defaultdict
from datetime import datetime

import psycopg2  # type: ignore
from asgiref.sync import sync_to_async
from django.db.models import Q
from telegram import Update, BotCommand
from telegram.ext import ContextTypes, CallbackContext

from bot.bot_logic.Settings.config import settings as SETTINGS
from bot.models import BotStatistic, TelegramUser, Appointment, AppointmentUser, Event, TempPassword

# Набор команд для меню чат-бота
commands = [
    BotCommand("start", "Начать работу бота"),
    BotCommand("help", "Дополнительная информация по по командам"),
    BotCommand("list_users", "Список пользователей"),
    BotCommand("list_events", "Список событий"),
    BotCommand("calendar", "Список встреч"),
    BotCommand("add_event", "Создать событие"),
    BotCommand("del_event", "Удалить событие"),
    BotCommand("confirm", "Подтвердить событие"),
    BotCommand("reject", "Отклонить событие"),
    BotCommand("invite", "Send message"),
    BotCommand("putite", "Send one-time password"),
    BotCommand("publish", "Сделать событие публичным"),
    BotCommand("list_publish", "Показать все публичные события"),
]



def generate_simple_password(length):
    """Generates a simple password of a given length."""
    all_characters = string.ascii_letters + string.digits
    password = ''.join(random.choice(all_characters) for _ in range(length))
    return password


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Функция запускает бота и выводит приветствие
    Также, регистрирует пользователя в чат-боте
    """
    user_id = update.effective_user.id
    user = update.effective_user
    username = user.username if user.username else user.first_name
    message_text = wash(update.message.text)

# Добавляем пользователя
    adduser, _ = await TelegramUser.objects.aget_or_create(
        nick_name = username,
        tg_id = user_id,
    )
    await adduser.asave()

    # Создать строку статистики для заданной даты если её нет
    stat, _ = await BotStatistic.objects.aget_or_create(
        date=datetime.now().date(),
        defaults={
            'user_count': 0,
            'event_count': 0,
            'edited_events': 0,
            'cancelled_events': 0,
            'tg_id' : adduser,
        }
    )
    # Увеличить на 1 счетчик уникальных пользователей
    await increment_statistic(stat, user_inc = 1)
    washed_username = wash(username)
    await context.bot.set_my_commands(commands)
    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*Добро пожаловать,* _{user_id}, {washed_username}_\\!\n Ваш текст: {message_text}",  # type: ignore
            parse_mode="MarkdownV2",
        )



async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
        Функция выводит помощь и также может зарегистрировать пользователя в боте
    """
    user_id = update.effective_user.id
    user = update.effective_user
    username = user.username if user.username else user.first_name

# Регистрируем пользователя в боте
    adduser, _ = await TelegramUser.objects.aget_or_create(
        nick_name = username,
        tg_id = user_id,
    )
    await adduser.asave()

    # Создать строку статистики для заданной даты если её нет
    stat, _ = await BotStatistic.objects.aget_or_create(
        date=datetime.now().date(),
        defaults={
            'user_count': 0,
            'event_count': 0,
            'edited_events': 0,
            'cancelled_events': 0,
            'tg_id': adduser,
        }
    )
    # Увеличить на 1 счетчик уникальных пользователей
    await increment_statistic(stat, user_inc = 1)

    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="""
            Это проект-питомец Дмитрия Петлина
            Для начала работы введите команду /start
            Для добавления события введите команду в следующем формате /add_event YYYY-MM-DD HH:MM Название события
            Для просмотра всех событий введите команду /list_events
            Для удаления события введите команду /del_event NN где NN это номер события из списка
            Пригласите другого пользователя на встречу, используя команду /invite <ID пользователя> <ID встречи>
            """,
        )

# Нужно для получения списка всех событий
@sync_to_async
def get_all_events_sync(user_id):
    return list(Event.objects.all().filter(
            Q(telegram_user=user_id)))

@sync_to_async
def get_event_str(events):
  return "\n".join([str(event) for event in events])

# Запрос списка событий
async def list_events(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    adduser = await TelegramUser.objects.aget(
        tg_id = user_id,
    )
    stat, _ = await BotStatistic.objects.aget_or_create(
        date=datetime.now().date(),
        defaults={
            'user_count': 0,
            'event_count': 0,
            'edited_events': 0,
            'cancelled_events': 0,
            'tg_id': adduser,
        }
    )

    # Увеличить на 1 счетчик уникальных пользователей
    await increment_statistic(stat, user_inc=1)

    all_events_str = ''
    events = await get_all_events_sync(adduser.user_id)
    listevents = await get_event_str(events)
    for event in listevents:
        all_events_str += event
    all_events_str = wash(all_events_str)

    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="\n*Все события из метода:*\n" + all_events_str,
            parse_mode="MarkdownV2",
        )


# Создание нового события
#TODO хорошо бы сделать проверку на корректность вводимых данных
async def add_event(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_text = update.message.text.replace("/add_event", "").strip()
    user_text_tmp = user_text.split()

# Разбираем аргументы из бота на куски: Дата, Время, текст
    if user_text:
        fdate, ftime, user_text_tmp = user_text_tmp[0], user_text_tmp[1], user_text_tmp[2:]
        user_text = " ".join(user_text_tmp).strip()
        formatted_date = datetime.strptime(fdate, "%Y-%m-%d")
        formatted_time = datetime.strptime(ftime, "%H:%M")

        #  Считали пользователя
        check_user = await TelegramUser.objects.aget(
            tg_id=user_id
        )

        # Добавили событие
        check_event, _ = await Event.objects.aget_or_create(
            name=user_text,
            date=formatted_date,
            time=formatted_time,
            telegram_user=check_user,
        )

        # Добавили встречу
        check_appo, _ = await Appointment.objects.aget_or_create(
            event=check_event,
            date=formatted_date,
            time=formatted_time,
            details=user_text,
            status="Ожидание"
        )

        #  Создали связку пользователя, встречи и через неё события
        add_appointments_user, _ = await AppointmentUser.objects.aget_or_create(
            appointment=check_appo,
            telegram_user=check_user,
            status="Ожидание"
        )

    else:
        user_text = "Пустая заметка"



    all_notes_str = await listing("events", check_user)
    all_notes_str = wash(all_notes_str)
    user_text = wash(user_text)

    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*Заметка* _{user_text}_ *была успешно добавлена\\!*\nВсе заметки:\n {all_notes_str}",
            parse_mode="MarkdownV2",
        )
        # Создать строку статистики для заданной даты
        stat, _ = await BotStatistic.objects.aget_or_create(
            date=datetime.now().date(),
            defaults={
                'user_count': 0,
                'event_count': 0,
                'edited_events': 0,
                'cancelled_events': 0,
                'tg_id': check_user,
            }
        )
        # Увеличить на 1 счетчик уникальных пользователей
        await increment_statistic(stat, event_inc = 1)

# Нужно для получения списка всех событий
@sync_to_async
def get_event_appo_sync(event_id):
    appos = list(AppointmentUser.objects.all().filter(
            Q(telegram_user=user_id) & (Q(status="Подтверждено") | Q(status="Ожидание"))))
    return "\n".join([str(appo) for appo in appos])

# Удаление события
async def del_event(update: Update, context: CallbackContext) -> None:
    """
        Удаляем событие. Вместе с ним удалятся связанные встречи и приглашения пользователей
    """
    user_id = update.effective_user.id
    user = update.effective_user
    username = user.username
    user_text = update.message.text.replace("/del_event", "").strip()
    result = ""

    # Загружаем пользователя
    select_user = await TelegramUser.objects.aget(
        tg_id=user_id
    )
    if user_text.isdigit():
        check_event = await Event.objects.filter(event_id=user_text, telegram_user=select_user).afirst()

        if check_event:
            await sync_to_async(check_event.delete)()

            # Создать строку статистики для заданной даты
            stat, _ = await BotStatistic.objects.aget_or_create(
                date=datetime.now().date(),
                defaults={
                    'user_count': 0,
                    'event_count': 0,
                    'edited_events': 0,
                    'cancelled_events': 0,
                    'tg_id': select_user,
                }
            )
            await increment_statistic(stat, deleted_inc = 1)

            result += f'*Заметка №{check_event.event_id}:* _"{check_event.name}"_* удалена*'
        else:
            result += f"Заметка с номером {user_text} не найдена"
    else:
        result = rf"Вы ввели {user_text}\. Здесь должен быть введён номер заметки для удаления\."

    all_notes_str = await listing("events", select_user)
    all_notes_str = wash(all_notes_str)

    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text= result + "\n*Все заметки:*\n" + all_notes_str,
            parse_mode="MarkdownV2",
        )

# Нужно для получения списка всех событий
@sync_to_async
def get_all_events_listing_sync(user_id):
    events =  list(Event.objects.all().filter(
            Q(telegram_user=user_id)))
    return "\n".join([str(event) for event in events])

# Процедура для формирования списка событий
async def listing(table, user_id):
    """
    Эта функция выводит список всех событий
    """
    all_events_str = ''
    listevents = await get_all_events_listing_sync(user_id)
    for event in listevents:
        all_events_str += event

    if all_events_str: return all_events_str
    else: return "Список ваших заметок пока пуст"

# Нужно для получения списка всех событий
@sync_to_async
def get_all_appo_sync(user_id):
    appos = list(AppointmentUser.objects.all().filter(
            Q(telegram_user=user_id) & (Q(status="Подтверждено") | Q(status="Ожидание"))))
    return "\n".join([str(appo) for appo in appos])


# Список моих встреч
async def my_appo(update: Update, context: CallbackContext) -> None:
    """
        Собираем приглашения в словарь такого формата:
        {date : [
            time: [ID, TEXT, STATUS]
            ]
        }
    """
    user_id = update.effective_user.id
    user = update.effective_user

    check_user = await TelegramUser.objects.aget(
        tg_id=user_id
    )

    appos = await get_all_appo_sync(check_user.user_id)
    appos = appos.split("\n")
    result = defaultdict(list)
    result_str = ""
    for appo in appos:
        try:
            appo_id, user_nick, appo_detail, appo_date, appo_time, appo_status = appo.split(" -:- ")
            appo_date = wash(appo_date)
            appo_time = wash(appo_time)
            value_list = [appo_id, wash(appo_detail), appo_status]
            result[appo_date].append({appo_time: value_list})
            for key, value in sorted(result.items()):
                result_str += f"*{key}*\n"
                for val in value:
                    for key2, value2 in sorted(val.items()):
                        result_str += f"   *{key2}*\n"
                        result_str += rf"\({value2[0]}\) "
                        result_str += f"{value2[1]} _{value2[2]}_\n"
                        result_str += r"\-" * 35
                        result_str += f"\n"
        except ValueError:
            result_str = "У вас нет записей в календаре"


    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text= "\n*Ваш календарь:*\n\n" + result_str,
            parse_mode="MarkdownV2",
        )


# Команда подтверждения встречи
async def confirm(update: Update, context: CallbackContext) -> None:
    await change_status_appo(update, context, "confirm")
    await my_appo(update, context)

# Команда отклонения встречи
async def reject(update: Update, context: CallbackContext) -> None:
    await change_status_appo(update, context, "reject")
    await my_appo(update, context)


# Изменяем статус приглашения в зависимости от ответа пользователя
async def change_status_appo(update: Update, context: CallbackContext, new_status) -> None:
    user_id = update.effective_user.id
    user = update.effective_user
    if new_status == "confirm":
        new_status_text = "Подтверждено"
    elif new_status == "reject":
        new_status_text = "Отменено"
    user_text = update.message.text.replace("/" + new_status, "").strip()

    select_user = await TelegramUser.objects.aget(
        tg_id=user_id
    )

    result = ""
    if user_text.isdigit():
        check_appo = await AppointmentUser.objects.aget(
            appointment = user_text,
            telegram_user = select_user.user_id,
            status = "Ожидание",
        )

        if check_appo:
            check_appo.status = new_status_text
            await check_appo.asave()

            # Создать строку статистики для заданной даты
            stat, _ = await BotStatistic.objects.aget_or_create(
                date=datetime.now().date(),
                defaults={
                    'user_count': 0,
                    'event_count': 0,
                    'edited_events': 0,
                    'cancelled_events': 0,
                    'tg_id': select_user,
                }
            )
            await increment_statistic(stat, edited_inc = 1)

            result += f'*Встреча №:* _"{user_id}"_* подтверждена*'
        else:
            result += f"Встреча с номером {user_text} не найдена"
    else:
        result = rf"Вы ввели {user_text}\. Здесь должен быть введён номер заметки для удаления\."

# Нужно для получения списка всех событий
@sync_to_async
def get_all_user_sync():
    users = list(TelegramUser.objects.all())
    return "\n".join([str(user) for user in users])


# Показываем список пользователей
async def list_users(update: Update, context: CallbackContext) -> None:
    list_user = await get_all_user_sync()
    list_user = wash(list_user)
    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text= "\n*Все пользователи:*\n" + list_user,
            parse_mode="MarkdownV2",
        )

# Приглашаем пользователя на встречу
async def invite_user(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user = update.effective_user
    username = user.username if user.username else user.first_name
    user_text = update.message.text.replace("/invite", "").strip()
    try:
        user_user, user_appo = user_text.split(" ")
        select_user = await TelegramUser.objects.aget(
            user_id=user_user
        )

        select_appo = await Appointment.objects.aget(
            event_id = user_appo,
        )


        all_user_appo = await get_all_appo_sync(select_user.user_id)

        all_user_appo_list = all_user_appo.split("\n")
        flag = True

        if len(all_user_appo_list) > 2:
            for appo in all_user_appo_list:
                _, _, _, date, time, _ = appo.split(" -:- ")
                if datetime.strptime(date, '%Y-%m-%d').date() == select_appo.date:
                    if datetime.strptime(time, '%H:%M:%S').time() == select_appo.time:
                        if update.effective_chat:
                            await context.bot.send_message(
                                chat_id=update.effective_chat.id,
                                text=f"\nУпользователя * {select_user.nick_name} * это время занято",
                                parse_mode="MarkdownV2",
                            )
                            flag = False


        if flag:
            #  Создали связку пользователя, встречи и через неё события
            add_appointments_user, _ = await AppointmentUser.objects.aget_or_create(
                appointment=select_appo,
                telegram_user=select_user,
                status="Ожидание"
            )

            invite_text = f"\nПользователь *{username}* приглашает вас на встречу *{select_appo.details}*, которая состоится *{select_appo.date}* в *{select_appo.time}*\nЧтобы принять встречу введите команду /confirm {add_appointments_user.appointment_id} \nДля отклонения встречи введите команду /reject {add_appointments_user.appointment_id}"
            invite_text = wash(invite_text)
            if update.effective_chat:
                await context.bot.send_message(
                    chat_id=select_user.tg_id,          #update.effective_chat.id,
                    text= invite_text,
                    parse_mode="MarkdownV2",
                )
            washed_nick_name = wash(select_user.nick_name)
            if update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text= "\n*Отправлено приглашение пользователю* " + washed_nick_name,
                    parse_mode="MarkdownV2",
                )
    except ValueError:
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="\n*Для корректного ввода команды используйте формат /invite \<ID пользователя\> \<ID встречи\>* ",
                parse_mode="MarkdownV2",
            )

# Получение (одноразового?) пароля для входа в личный кабинет на сайте
async def putite(update: Update, context: CallbackContext) -> None:
    one_time_password = generate_simple_password(10)
    user_id = update.effective_user.id
    user = await TelegramUser.objects.aget(tg_id=user_id)
    await TempPassword.objects.aupdate_or_create(
        tg = user,
        defaults = {"password" : one_time_password}
    )
    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="\n*Ваш одноразовый пароль* " + one_time_password,
            parse_mode="MarkdownV2",
        )


# Делаем событие публичным
async def publish(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user = update.effective_user
    username = user.username if user.username else user.first_name
    event_to_publish = update.message.text.replace("/publish", "").strip()
    select_user = await TelegramUser.objects.aget(
        tg_id=user_id
    )

    select_event = await Event.objects.aget(
        event_id = event_to_publish,
        telegram_user = select_user
    )
    msg = ""
    if select_event:
        if not select_event.public:
            select_event.public = "True"
            await select_event.asave()
            text = wash(select_event.name)
            msg = f"Событие *{text}* стало общедоступным\!"
        else:
            msg = f"Событие *{event_to_publish}* уже общедоступное\!"
    else:
        msg = f"Событие *{event_to_publish}* не существует\!"

    if update.effective_chat:
        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = msg,
            parse_mode = "MarkdownV2",
        )


# Список публичных событий
@sync_to_async
def get_all_publish_events_sync():
    return list(Event.objects.all().filter(
            Q(public=True)))

async def list_publish(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    adduser = await TelegramUser.objects.aget(
        tg_id = user_id,
    )
    stat, _ = await BotStatistic.objects.aget_or_create(
        date=datetime.now().date(),
        defaults={
            'user_count': 0,
            'event_count': 0,
            'edited_events': 0,
            'cancelled_events': 0,
            'tg_id': adduser,
        }
    )

    # Увеличить на 1 счетчик уникальных пользователей
    await increment_statistic(stat, user_inc=1)

    all_events_str = ''
    events = await get_all_publish_events_sync()
    listevents = await get_event_str(events)
    for event in listevents:
        all_events_str += event
    all_events_str = wash(all_events_str)

    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="\n*Все события из метода:*\n" + all_events_str,
            parse_mode="MarkdownV2",
        )

def wash(text: str):
    """
        Экранирование символов для совместимости с MarkdownV2
    """
    special_chars = "_*[]()~'>#+-=|{}.!"
    pattern = "[" + re.escape(special_chars) + "]"
    return re.sub(pattern, lambda m: "\\" + m.group(), text)


async def increment_statistic(obj: BotStatistic, user_inc: int = 0, event_inc: int = 0, edited_inc: int = 0, deleted_inc: int = 0) -> None:
    if (
        user_inc == 0
        and event_inc == 0
        and edited_inc == 0
        and deleted_inc == 0
    ):
        raise Exception("Что-то должно быть больше нуля")
    obj.user_count += user_inc
    obj.event_count += event_inc
    obj.edited_events += edited_inc
    obj.cancelled_events += deleted_inc
    await obj.asave()
