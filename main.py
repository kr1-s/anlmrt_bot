import logging
import sqlite3
import time
import schedule

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler, ConversationHandler, MessageHandler, \
    filters, CallbackQueryHandler, Job, JobQueue

# Добавил коммент2222

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

conn = sqlite3.connect('anlmrt_db.db', check_same_thread=False)
cursor = conn.cursor()


async def get_chat(update: Update, context: CallbackContext):
    user_id = update.effective_message.from_user.id
    chats_list = conn.execute('select title, chat_id from chat '
                              'where chat_id in ('
                              'select chat_id from chat_members where user_id= {}'
                              ') and title is not null '.format(user_id)).fetchall()
    button = [[]]
    chat_dict = {}
    count = 0
    for el in chats_list:
        button[0].append(InlineKeyboardButton(chats_list[count][0], callback_data=chats_list[count][1]))
        chat_dict[chats_list[count][1]] = chats_list[count][0]
        count += 1

    reply_markup = InlineKeyboardMarkup(button)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Выберите чат в котором будет встреча:",
                                   reply_markup=reply_markup)
    try:
        context.user_data["change"]
        context.user_data["new_value"] = "chat"
        return "accept"
    except:
        context.user_data["chat_list"] = chat_dict
        return "date"


async def get_date(update: Update, context: CallbackContext):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Отправьте дату и время в формате: \"дд.мм.гг чч:мм\", например - "
                                        "\"26.05.22 16:30\" ")
    try:
        context.user_data["change"]
        context.user_data["new_value"] = "date"
        return "accept"
    except:
        context.user_data["chat"] = update.callback_query.data  # сохраняем id чата встречи
        return "label"


async def get_label(update: Update, context: CallbackContext):
    button = ReplyKeyboardMarkup([["Оставить пустым"]], resize_keyboard=True, one_time_keyboard=True)
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Отправьте тему встречи, если хотите оставить пустым, нажмите кнопку",
                                   reply_markup=button)
    try:
        context.user_data["change"]
        context.user_data["new_value"] = "label"
        return "accept"
    except:
        context.user_data["date"] = update.effective_message.text  # сохраняем дату встречи
        return "discription"


async def get_discription(update: Update, context: CallbackContext):
    button = ReplyKeyboardMarkup([["Оставить пустым"]], resize_keyboard=True, one_time_keyboard=True)
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Отправьте описание встречи, если хотите оставить пустым, нажмите кнопку",
                                   reply_markup=button)
    try:
        context.user_data["change"]
        context.user_data["new_value"] = "discription"
        return "accept"
    except:
        context.user_data["label"] = update.effective_message.text  # сохраняем название встречи
        return "members"


async def get_members(update: Update, context: CallbackContext):
    button = ReplyKeyboardMarkup([["Оставить пустым"]], resize_keyboard=True, one_time_keyboard=True)
    print(context.user_data["chat"])
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Отметье людей, которых хотите пригласить через \"@\", "
                                        "если хотите оставить пустым, нажмите кнопку",
                                   reply_markup=button)
    try:
        context.user_data["change"]
        context.user_data["new_value"] = "members"
        return "accept"
    except:
        context.user_data["discription"] = update.effective_message.text  # сохраняем описание встречи
        return "accept"


async def change_conversation(update: Update, context: CallbackContext):
    context.user_data["change"] = True
    button = ReplyKeyboardMarkup([["Чат", "Тема", "Описание"], ["Дата", "Участники"]], resize_keyboard=True,
                                 one_time_keyboard=True)
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Что выхотите поменять?",
                                   reply_markup=button)

    return "change"


async def accept_data(update: Update, context: CallbackContext):
    if "change" not in context.user_data:
        context.user_data["members"] = update.effective_message.text  # сохраняем участников встречи
    else:
        # try:
        #     #TODO присваивается последнее сообщение в чате, исправить
        #     context.user_data[context.user_data["new_value"]] = update.effective_message.text
        # except:
        #     print(update.callback_query.data)
        #     context.user_data[context.user_data["new_value"]] = update.callback_query.data
        if update.effective_message.from_user.is_bot:
            print(update.callback_query.data)
            context.user_data[context.user_data["new_value"]] = update.callback_query.data
        else:
            context.user_data[context.user_data["new_value"]] = update.effective_message.text

    for el in context.user_data:
        if context.user_data[el] == "Оставить пустым":
            context.user_data[el] = None

    text = """Подтвердите встречу
    <b>Название чата:</b> {}
    <b>Тема встречи:</b> {label}
    <b>Описание:</b> {discription}
    <b>Дата: </b>{date}
    <b>Участники:</b> {members}
    """.format(context.user_data["chat_list"].get(context.user_data["chat"]), **context.user_data)
    button = ReplyKeyboardMarkup([["Подтвердить", "Изменить"], ["Отменить"]], resize_keyboard=True,
                                 one_time_keyboard=True)
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=text,
                                   parse_mode=ParseMode.HTML,
                                   reply_markup=button)
    return "commit"


async def commit_conversation(update: Update, context: CallbackContext):
    co = context.user_data
    author = update.effective_message.from_user.id
    cursor.execute(
        'INSERT INTO conversation (label, date, discription, author, member, chat_id) VALUES (?, ?, ?, ?, ?, ?)',
        (co["label"], co["date"], co["discription"], author, co["members"], co["chat"]))
    conn.commit()
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Встреча назначена",
                                   reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def return_error(update: Update, context: CallbackContext):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Неверный формат, попробуйте ещё раз.")


async def end(update: Update, context: CallbackContext):
    return ConversationHandler.END


async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_message.from_user
    user = update.effective_message.from_user
    user_id = user.id
    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    # TODO Добавить проверку на существующего пользователя
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Привет!")
    cursor.execute('INSERT INTO user (id, username, first_name, last_name) VALUES (?, ?, ?, ?)',
                   (user_id, username, first_name, last_name))


async def register_chat(update: Update, context: CallbackContext):
    chat = update.effective_message.chat
    chat_id = chat.id
    user_id = update.effective_message.from_user.id
    if chat.title is None:
        title = chat.username
    elif chat.username is None:
        title = chat.title
    first_name = chat.first_name
    last_name = chat.last_name
    await context.bot.send_message(chat_id=chat_id, text="Ты зарегистрирован(а) в чате.")
    cursor.execute('INSERT INTO chat_members (user_id, chat_id) VALUES (?, ?)',
                   (user_id, chat_id))
    cursor.execute('INSERT INTO chat (chat_id, title, first_name, last_name) VALUES (?, ?, ?, ?)',
                   (chat_id, title, first_name, last_name))
    conn.commit()


# async def chat(update: Update, context: CallbackContext):
#     members = cursor.execute('select * from conversation').fetchall()
#     chat_id = cursor.execute(('select chat_id from chat where title like "{}"'.format(members[0][6]))).fetchall()[0][0]
#     text = """{} встреча начнётся через 15 минут.""".format(members[0][5])
#     await context.bot.send_message(chat_id=chat_id, text=text)


async def alarm(update: Update, context: CallbackContext):
    job = context.job
    await context.bot.send_message(job.chat_id, text=f"Встреча {job.label} началась. \nУчастники: {job.members}")


async def create_job(update: Update, context: CallbackContext):
    conversations = cursor.execute(
        'select label, date, description, author, member, chat_id from conversation').fetchall()
    for conv in conversations:
        print(conv)
    # JobQueue.run_once()


def job():
    print("I'm working...")




if __name__ == '__main__':
    application = ApplicationBuilder().token('5116521471:AAGyvwDZw-yFq7R_Pl5YDRHid77P4DwBu6Y').build()

    start_handler = CommandHandler('start', start)
    register_chat = CommandHandler("join_chat", register_chat)
    test = CommandHandler("chat", create_job)
    timer = ConversationHandler(
        entry_points=[CommandHandler('set_timer', get_chat)],
        states={
            "date": [CallbackQueryHandler(get_date)],
            "label": [MessageHandler(filters.Regex(r"^\s*\d\d\.\d\d\.\d\d\s*\d\d\:\d\d\s*$"), get_label),
                      MessageHandler(filters.ALL, return_error)],
            "discription": [MessageHandler(filters.ALL, get_discription)],
            "members": [MessageHandler(filters.ALL, get_members)],
            "accept": [MessageHandler(filters.ALL, accept_data),
                       CallbackQueryHandler(accept_data)],
            "commit": [MessageHandler(filters.Regex("Подтвердить"), commit_conversation),
                       MessageHandler(filters.Regex("Изменить"), change_conversation),
                       MessageHandler(filters.Regex("Отменить"), end)],
            "change": [MessageHandler(filters.Regex("Чат"), get_chat),
                       MessageHandler(filters.Regex("Тема"), get_label),
                       MessageHandler(filters.Regex("Описание"), get_discription),
                       MessageHandler(filters.Regex("Дата"), get_date),
                       MessageHandler(filters.Regex("Участники"), get_members)]
        },
        fallbacks=[CommandHandler('start', start)])
    application.add_handler(start_handler)
    application.add_handler(register_chat)
    application.add_handler(timer)
    application.add_handler(test)
    application.run_polling()
