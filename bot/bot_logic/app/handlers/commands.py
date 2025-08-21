import psycopg2  # type: ignore
import re
from datetime import datetime
from telegram import Update, BotCommand
from telegram.ext import ContextTypes, CallbackContext
from bot.bot_logic.Settings.config import settings as SETTINGS
from bot.models import BotStatistic, TelegramUser, Appointment, AppointmentUser, Event
from asgiref.sync import sync_to_async

# Набор команд для меню чат-бота
commands = [
    BotCommand("start", "Начать работу бота"),
    BotCommand("help", "Дополнительная информация по по командам"),
    BotCommand("list_events", "Список событий"),
    BotCommand("my_appo", "Список встреч"),
    BotCommand("add_event", "Создать событие"),
    BotCommand("del_event", "Удалить событие"),
    BotCommand("confirm", "Подтвердить событие"),
]



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Функция запускает бота и выводит приветствие
    Также, регистрирует пользователя в чат-боте
    """
    # Создать строку статистики для заданной даты если её нет
    stat, _ = await BotStatistic.objects.aget_or_create(
        date=datetime.now().date(),
        defaults={
            'user_count': 0,
            'event_count': 0,
            'edited_events': 0,
            'cancelled_events': 0,
        }
    )
    # Увеличить на 1 счетчик уникальных пользователей
    await increment_statistic(stat, user_inc = 1)

    user_id = update.effective_user.id
    user = update.effective_user
    username = user.username
    message_text = wash(update.message.text)

# Добавляем пользователя
    adduser, _ = await TelegramUser.objects.aget_or_create(
        nick_name = username,
        tg_id = user_id,
    )
    await adduser.asave()

    await context.bot.set_my_commands(commands)
    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*Добро пожаловать,* _{user_id}, {username}_\\!\n Ваш текст: {message_text}",  # type: ignore
            parse_mode="MarkdownV2",
        )



async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
        Функция выводит помощь и также может зарегистрировать пользователя в боте
    """

    # Создать строку статистики для заданной даты если её нет
    stat, _ = await BotStatistic.objects.aget_or_create(
        date=datetime.now().date(),
        defaults={
            'user_count': 0,
            'event_count': 0,
            'edited_events': 0,
            'cancelled_events': 0,
        }
    )
    # Увеличить на 1 счетчик уникальных пользователей
    await increment_statistic(stat, user_inc = 1)

    user_id = update.effective_user.id
    user = update.effective_user
    username = user.username

# Регистрируем пользователя в боте
    adduser, _ = await TelegramUser.objects.aget_or_create(
        nick_name = username,
        tg_id = user_id,
    )
    await adduser.asave()

    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="""
            Это проект-питомец Дмитрия Петлина
            Для начала работы введите команду /start
            Для добавления события введите команду в следующем формате /add_event YYYY-MM-DD HH:MM:SS Название события
            Для просмотра всех событий введите команду /list_events
            Для удаления события введите команду /del_event NN где NN это номер события из списка
            """,
        )

# Нужно для получения списка всех событий
@sync_to_async
def get_all_events_sync():
    return list(Event.objects.all())

async def list_events(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    stat, _ = await BotStatistic.objects.aget_or_create(
        date=datetime.now().date(),
        defaults={
            'user_count': 0,
            'event_count': 0,
            'edited_events': 0,
            'cancelled_events': 0,
        }
    )

    # Увеличить на 1 счетчик уникальных пользователей
    await increment_statistic(stat, user_inc=1)

    all_events_str = ''
    events = await get_all_events_sync()
    listevents = "\n".join([str(event) for event in events])
    for event in listevents:
        all_events_str += event
    all_events_str = wash(all_events_str)

    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="\n*Все события из метода:*\n" + all_events_str,
            parse_mode="MarkdownV2",
        )


async def add_event(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_text = update.message.text.replace("/add_event", "").strip()
    user_text_tmp = user_text.split()

# Разбираем аргументы из бота на куски: Дата, Время, текст
    if user_text:
        fdate, ftime, user_text_tmp = user_text_tmp[0], user_text_tmp[1], user_text_tmp[2:]
        user_text = " ".join(user_text_tmp).strip()
        formatted_date = datetime.strptime(fdate, "%Y-%m-%d")
        formatted_time = datetime.strptime(ftime, "%H:%M:%S")

        # Добавили событие
        addevents, _ = await Event.objects.aget_or_create(
            name=user_text,
            date=formatted_date,
            time=formatted_time,
        )
        await addevents.asave()
        # Считали событие, чтобы получить его как объект и ID
        check_event = await Event.objects.aget(
            name=user_text,
            date=formatted_date,
            time=formatted_time,
        )
        # Добавили встречу
        add_appointments, _ = await Appointment.objects.aget_or_create(
            event=check_event,
            date=formatted_date,
            time=formatted_time,
            details=user_text,
            status="Ожидание"
        )
        await add_appointments.asave()
        # Считали встречу, чтобы получить объект и его ID
        check_appo = await Appointment.objects.aget(
            event=check_event,
            date=formatted_date,
            time=formatted_time,
            details=user_text,
            status="Ожидание"
        )
        #  Считали пользователя
        check_user = await TelegramUser.objects.aget(
            tg_id=user_id
        )
        #  Создали связку пользователя, встречи и через неё события
        add_appointments_user, _ = await AppointmentUser.objects.aget_or_create(
            appointment=check_appo,
            telegram_user=check_user,
            status="Ожидание"
        )
        await add_appointments_user.asave()

    else:
        user_text = "Пустая заметка"



    all_notes_str = await listing("events", user_id)
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
            }
        )
        # Увеличить на 1 счетчик уникальных пользователей
        await increment_statistic(stat, event_inc = 1)


async def del_event(update: Update, context: CallbackContext) -> None:
    """
        Удаляем событие. Вместе с ним удалятся связанные встречи и приглашения пользователей
    """
    user_id = update.effective_user.id
    user = update.effective_user
    username = user.username
    user_text = update.message.text.replace("/del_event", "").strip()
    result = ""
    if user_text.isdigit():
        check_event = await Event.objects.aget(
            event_id = user_text,
        )

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
                }
            )
            await increment_statistic(stat, deleted_inc = 1)

            result += f'*Заметка №{check_event.event_id}:* _"{check_event.name}"_* удалена*'
        else:
            result += f"Заметка с номером {user_text} не найдена"
    else:
        result = rf"Вы ввели {user_text}\. Здесь должен быть введён номер заметки для удаления\."

    all_notes_str = await listing("events", user_id)
    all_notes_str = wash(all_notes_str)

    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text= result + "\n*Все заметки:*\n" + all_notes_str,
            parse_mode="MarkdownV2",
        )

        # check_events,


async def listing(table, user_id):
    """
    Эта функция выводит список всех событий
    """
    all_events_str = ''
    events = await get_all_events_sync()
    listevents = "\n".join([str(event) for event in events])
    for event in listevents:
        all_events_str += event

    if all_events_str: return all_events_str
    else: return "Список ваших заметок пока пуст"

# Нужно для получения списка всех событий
@sync_to_async
def get_all_appo_sync(tg_id):
    appos = list(AppointmentUser.objects.all().filter(telegram_user=5))
    return "\n".join([str(appo) for appo in appos])

async def my_appo(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user = update.effective_user
    username = user.username

    check_user = await TelegramUser.objects.aget(
        tg_id=user_id
    )

    all_appo_str = ''
    appos = await get_all_appo_sync(check_user.tg_id)

    for appo in appos:
        all_appo_str += appo

    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text= "\n*Все встречи:*\n" + all_appo_str,
            #parse_mode="MarkdownV2",
        )


async def confirm(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user = update.effective_user
    user_text = update.message.text.replace("/confirm", "").strip()

    result = ""
    if user_text.isdigit():
        check_appo = await AppointmentUser.objects.aget(
            appointment = user_text,
            status = "Ожидание",
        )

        if check_appo:
            check_appo.status="Подтверждено"
            await check_appo.asave()

            # Создать строку статистики для заданной даты
            stat, _ = await BotStatistic.objects.aget_or_create(
                date=datetime.now().date(),
                defaults={
                    'user_count': 0,
                    'event_count': 0,
                    'edited_events': 0,
                    'cancelled_events': 0,
                }
            )
            await increment_statistic(stat, edited_inc = 1)

            result += f'*Встреча №:* _"{user_id}"_* подтверждена*'
        else:
            result += f"Встреча с номером {user_text} не найдена"
    else:
        result = rf"Вы ввели {user_text}\. Здесь должен быть введён номер заметки для удаления\."

    await my_appo(update, context)




def wash(text: str):
    """
        Экранирование символов для совместимости с MarkdownV2
    """
    special_chars = [
        "_",
        "*",
        "[",
        "]",
        "(",
        ")",
        "~",
        "'",
        ">",
        "#",
        "+",
        "-",
        "=",
        "|",
        "{",
        "}",
        ".",
        "!",
    ]
    pattern = "[" + re.escape("".join(special_chars)) + "]"
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
