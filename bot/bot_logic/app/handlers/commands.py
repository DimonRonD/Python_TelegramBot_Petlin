import psycopg2  # type: ignore
import re
from datetime import datetime
from telegram import Update, BotCommand
from telegram.ext import ContextTypes, CallbackContext
from bot.bot_logic.Settings.config import settings as SETTINGS
from bot.models import BotStatistic

# Набор команд для меню чат-бота
commands = [
    BotCommand("start", "Начать работу бота"),
    BotCommand("help", "Дополнительная информация по по командам"),
    BotCommand("add_note", "Создать заметку"),
    BotCommand("list_notes", "Список заметок"),
    BotCommand("del_note", "Удалить заметку"),
    BotCommand("add_event", "Создать событие"),
    BotCommand("list_events", "Список событий"),
    BotCommand("del_event", "Удалить событие"),
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Функция запускает бота и выводит приветствие
    """
    # Создать строку статистики для заданной даты
    BotStatistic.objects.create(
        date=datetime.now().date(),
        user_count=0,
        event_count=0,
        edited_events=0,
        cancelled_events=0,
    )

    # Увеличить на 1 счетчик созданных событий
    stat = BotStatistic.objects.filter(date=datetime.now().date()).get()
    stat.user_count += 1
    stat.save()

    user_id = update.effective_user.id
    user = update.effective_user
    username = user.username
    message_text = wash(update.message.text)
    await context.bot.set_my_commands(commands)
    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*Добро пожаловать,* _{user_id}, {username}_\\!\n Ваш текст: {message_text}",  # type: ignore
            parse_mode="MarkdownV2",
        )


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="""
            Это проект-питомец Дмитрия Петлина
            Для начала работы введите команду /start
            Для добавления заметки введите команду /add_note
            """,
        )


async def list_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    all_notes_str = listing("notes", user_id)

    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="\n*Все заметки:*\n" + all_notes_str,
            parse_mode="MarkdownV2",
        )


async def add_note(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user = update.effective_user
    username = user.username

    user_text = update.message.text.replace("/add_note", "").strip()

    now_time = datetime.now()
    formatted_time = now_time.strftime("%H:%M:%S")

    if not user_text:
        user_text = "Пустая заметка"
    conn = psycopg2.connect(
        host=SETTINGS.host,
        database=SETTINGS.database,
        user=SETTINGS.username,
        password=SETTINGS.password,
    )
    try:
        cursor = conn.cursor()
    except psycopg2.OperationalError:
        print(psycopg2.OperationalError)

    cursor.execute(
        f"insert into notes (uid, uname, date_note, note, time_note) values ({user_id}, '{username}', CURRENT_DATE, '{user_text}', '{formatted_time}');"
    )
    conn.commit()
    cursor.close()
    conn.close()

    all_notes_str = listing("notes", user_id)
    user_text = wash(user_text)

    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*Заметка* _{user_text}_ *была успешно добавлена\\!*\nВсе заметки:\n {all_notes_str}",
            parse_mode="MarkdownV2",
        )


async def del_note(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user = update.effective_user
    username = user.username
    user_text = update.message.text.replace("/del_note", "").strip()
    result = ""
    if user_text.isdigit():
        conn = psycopg2.connect(
            host=SETTINGS.host,
            database=SETTINGS.database,
            user=SETTINGS.username,
            password=SETTINGS.password,
        )
        try:
            cursor = conn.cursor()
        except psycopg2.OperationalError:
            print(psycopg2.OperationalError)
        cursor.execute(
            f"SELECT * FROM notes WHERE uid={user_id} and id={user_text};", (1,)
        )

        rows = cursor.fetchall()
        if rows:
            cursor.execute(f"DELETE FROM notes WHERE uid={user_id} and id={user_text};")
            conn.commit()
            result += f'*Заметка №{str(rows[0][0])}:* _"{str(rows[0][4])}"_* удалена*'
        else:
            result += f"Сочетание {user_text} и {user_id} для пользователя {username} не найдено"
        cursor.close()
        conn.close()
    else:
        result = f"Вы ввели {user_text}\\. Здесь должен быть введён номер заметки для удаления\\."

    all_notes_str = listing("notes", user_id)

    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=result + "\n*Все заметки:*\n" + all_notes_str,
            parse_mode="MarkdownV2",
        )


async def list_events(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    all_notes_str = listing("events", user_id)

    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="\n*Все события:*\n" + all_notes_str,
            parse_mode="MarkdownV2",
        )


async def add_event(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user = update.effective_user
    username = user.username

    user_text = update.message.text.replace("/add_note", "").strip()

    now_time = datetime.now()
    formatted_time = now_time.strftime("%H:%M:%S")

    if not user_text:
        user_text = "Пустая заметка"
    conn = psycopg2.connect(
        host=SETTINGS.host,
        database=SETTINGS.database,
        user=SETTINGS.username,
        password=SETTINGS.password,
    )
    try:
        cursor = conn.cursor()
    except psycopg2.OperationalError:
        print(psycopg2.OperationalError)

    cursor.execute(
        f"insert into events (uid, uname, event_date, event_time, details) values ({user_id}, "
        f"'{username}', CURRENT_DATE, '{formatted_time}', '{user_text}');"
    )
    conn.commit()
    cursor.close()
    conn.close()

    all_notes_str = listing("events", user_id)
    user_text = wash(user_text)

    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*Заметка* _{user_text}_ *была успешно добавлена\\!*\nВсе заметки:\n {all_notes_str}",
            parse_mode="MarkdownV2",
        )


async def del_event(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user = update.effective_user
    username = user.username
    user_text = update.message.text.replace("/del_event", "").strip()
    result = ""
    if user_text.isdigit():
        conn = psycopg2.connect(
            host=SETTINGS.host,
            database=SETTINGS.database,
            user=SETTINGS.username,
            password=SETTINGS.password,
        )
        try:
            cursor = conn.cursor()
        except psycopg2.OperationalError:
            print(psycopg2.OperationalError)
        cursor.execute(
            f"SELECT * FROM events WHERE uid={user_id} and id={user_text};", (1,)
        )

        rows = cursor.fetchall()
        if rows:
            cursor.execute(
                f"DELETE FROM events WHERE uid={user_id} and id={user_text};"
            )
            conn.commit()
            result += f'*Заметка №{str(rows[0][0])}:* _"{str(rows[0][5])}"_* удалена*'
        else:
            result += f"Сочетание {user_text} и {user_id} для пользователя {username} не найдено"
        cursor.close()
        conn.close()
    else:
        result = rf"Вы ввели {user_text}\. Здесь должен быть введён номер заметки для удаления\."

    all_notes_str = listing("events", user_id)

    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=result + "\n*Все заметки:*\n" + all_notes_str,
            parse_mode="MarkdownV2",
        )


def listing(table, user_id):

    conn = psycopg2.connect(
        host=SETTINGS.host,
        database=SETTINGS.database,
        user=SETTINGS.username,
        password=SETTINGS.password,
    )
    try:
        cursor = conn.cursor()
    except psycopg2.OperationalError:
        print(psycopg2.OperationalError)

    cursor.execute(f"SELECT * FROM {table} WHERE uid={user_id};", (1,))

    # Fetch all results
    rows = cursor.fetchall()
    all_notes_str = ""
    cursor.close()
    conn.close()

    if rows:
        if table == "notes":
            for row in sorted(rows):
                row_id = wash(str(row[0]))
                row_date = wash(str(row[3]))
                row_text = wash(str(row[4]))
                row_time = wash(str(row[6]))
                all_notes_str += (
                    "*"
                    + row_id
                    + "*"
                    + "\t"
                    + row_date
                    + "\t"
                    + row_time
                    + "\t"
                    + "_"
                    + row_text
                    + "_"
                    + "\n"
                )
            return all_notes_str
        else:
            for row in sorted(rows):
                row_id = wash(str(row[0]))
                row_date = wash(str(row[3]))
                row_time = wash(str(row[4]))
                row_text = wash(str(row[5]))
                all_notes_str += (
                    "*"
                    + row_id
                    + "*"
                    + "\t"
                    + row_date
                    + "\t"
                    + row_time
                    + "\t"
                    + "_"
                    + row_text
                    + "_"
                    + "\n"
                )
            return all_notes_str
    else:
        return "Список ваших заметок пока пуст"


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
