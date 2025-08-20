import psycopg2  # type: ignore
import re
from datetime import datetime
from psycopg2 import sql
from telegram import Update, BotCommand
from telegram.ext import ContextTypes, CallbackContext
from bot.bot_logic.Settings.config import settings as SETTINGS
from bot.models import BotStatistic, TelegramUser, Appointment, AppointmentUser, Event
from asgiref.sync import sync_to_async

# Набор команд для меню чат-бота
commands = [
    BotCommand("start", "Начать работу бота"),
    BotCommand("help", "Дополнительная информация по по командам"),
    BotCommand("add_event", "Создать событие"),
    BotCommand("list_events", "Список событий"),
    BotCommand("del_event", "Удалить событие"),
]



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Функция запускает бота и выводит приветствие
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

    adduser, _ = await TelegramUser.objects.aget_or_create(
        nick_name = username,
        tg_id = user_id,
        create_date = datetime.now(),
    )
    await adduser.asave()

    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="""
            Это проект-питомец Дмитрия Петлина
            Для начала работы введите команду /start
            Для добавления заметки введите команду /add_note
            """,
        )

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

    now_time = datetime.now()
    formatted_date = now_time.strftime("%Y-%m-%d")
    formatted_time = now_time.strftime("%H:%M:%S")

    if not user_text:
        user_text = "Пустая заметка"

    addevents, _ = await Event.objects.aget_or_create(
        name = user_text,
        date = formatted_date,
        time = formatted_time,
    )
    await addevents.asave()

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

    all_events_str = ''
    events = await get_all_events_sync()
    listevents = "\n".join([str(event) for event in events])
    for event in listevents:
        all_events_str += event

    if all_events_str: return all_events_str
    else: return "Список ваших заметок пока пуст"


def wash(text: str):
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
