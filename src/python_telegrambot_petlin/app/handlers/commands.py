from telegram import Update, BotCommand
from telegram.ext import ContextTypes, CallbackContext
import psycopg2  # type: ignore
import re
from src.python_telegrambot_petlin.Settings.config import settings as SETTINGS

commands = [
    BotCommand("start", "Начать работу бота"),
    BotCommand("help", "Дополнительная информация по по командам"),
    BotCommand("add_note", "Создать заметку"),
    BotCommand("list_notes", "Список заметок"),
    BotCommand("del_note", "Удалить заметку"),
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = update.effective_user
    username = user.username
    message_text = wash(update.message.text)
    await context.bot.set_my_commands(commands)
    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*Добро пожаловать,* _{user_id}, {username}_\!\n Ваш текст: {message_text}", # type: ignore
            parse_mode='MarkdownV2'
        )

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=
            """
            Это проект-питомец Дмитрия Петлина
            Для начала работы введите команду /start
            Для добавления заметки введите команду /add_note
            """
        )

async def list_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    all_notes_str = listing(user_id)

    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text= all_notes_str,
            parse_mode='MarkdownV2'
        )

async def add_note(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user = update.effective_user
    username = user.username

    user_text = update.message.text.replace('/add_note', '').strip()

    if not user_text:
        user_text = 'Пустая заметка'
    conn = psycopg2.connect(host=SETTINGS.host, database=SETTINGS.database, user=SETTINGS.username, password=SETTINGS.password)
    try:
        cursor = conn.cursor()
    except psycopg2.OperationalError:
        print(psycopg2.OperationalError)

    cursor.execute(f'insert into notes (uid, uname, date_note, note) values ({user_id}, \'{username}\', CURRENT_DATE, \'{user_text}\');')
    conn.commit()
    cursor.close()
    conn.close()

    all_notes_str = listing(user_id)
    user_text = wash(user_text)

    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*Заметка* _{user_text}_ *была успешно добавлена\!*\nВсе заметки:\n {all_notes_str}",
            parse_mode='MarkdownV2'
        )




async def del_note(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user = update.effective_user
    username = user.username
    user_text = update.message.text.replace('/del_note', '').strip()
    result = ''
    if user_text.isdigit():
        conn = psycopg2.connect(host=SETTINGS.host, database=SETTINGS.database, user=SETTINGS.username, password=SETTINGS.password)
        try:
            cursor = conn.cursor()
        except psycopg2.OperationalError:
            print(psycopg2.OperationalError)
        cursor.execute(f'SELECT * FROM notes WHERE uid={user_id} and id={user_text};', (1,))

        rows = cursor.fetchall()
        if rows:
            cursor.execute(f'DELETE FROM notes WHERE uid={user_id} and id={user_text};')
            conn.commit()
            result += (f'*Заметка №{str(rows[0][0])}:* _\"{str(rows[0][4])}\"_* удалена*')
        else:
            result += (f'Сочетание {user_text} и {user_id} для пользователя {username} не найдено')
        cursor.close()
        conn.close()
    else:
        result = (f'Вы ввели {user_text}\. Здесь должен быть введён номер заметки для удаления\.')

    all_notes_str = listing(user_id)

    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=result + '\n*Все заметки:*\n' + all_notes_str,
            parse_mode='MarkdownV2'
        )


def listing(user_id):


    conn = psycopg2.connect(host=SETTINGS.host, database=SETTINGS.database, user=SETTINGS.username, password=SETTINGS.password)
    try:
        cursor = conn.cursor()
    except psycopg2.OperationalError:
        print(psycopg2.OperationalError)

    cursor.execute(f'SELECT * FROM notes WHERE uid={user_id};', (1,))

    # Fetch all results
    rows = cursor.fetchall()
    all_notes_str = ''
    for row in sorted(rows):
        row_id = wash(str(row[0]))
        row_date = wash(str(row[3]))
        row_text = wash(str(row[4]))
        all_notes_str += '*' + row_id + '*' + '\t' + row_date + '\t' + '_' + row_text + '_' + '\n'

    cursor.close()
    conn.close()

    return all_notes_str

def wash(text: str):
    special_chars = ['_', '*', '[', ']', '(', ')', '~', "'", '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    pattern = '[' + re.escape(''.join(special_chars)) + ']'
    return re.sub(pattern, lambda m: '\\' + m.group(), text)
