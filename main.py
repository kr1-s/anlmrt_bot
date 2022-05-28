import logging
import sqlite3

from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler, ConversationHandler, MessageHandler, \
    filters

DATE, INPUT_DATE = range(2)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

conn = sqlite3.connect('C:/Users/skrivov/Desktop/SQLiteStudio/anlmrt_db.db', check_same_thread=False)
cursor = conn.cursor()


async def set_date(update: Update, context: CallbackContext):

    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Отправьте дату и время в формате: \"дд.мм.гг чч:мм\", например - "
                                        "\"26.05.2022 16:30\" ")

    return INPUT_DATE


async def check(update: Update, context: CallbackContext):
    msg = update.effective_message.text
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Дата верна? \n\n{}".format(msg))
    return ConversationHandler.END


async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_message.from_user
    user = update.effective_message.from_user
    user_id = user.id
    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Привет!")
    cursor.execute('INSERT INTO user (id, username, first_name, last_name) VALUES (?, ?, ?, ?)',
                   (user_id, username, first_name, last_name))
    conn.commit()


async def accept_date(update: Update, context: CallbackContext):
    chat_id = update.effective_message.chat_id
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Привет!")


if __name__ == '__main__':
    application = ApplicationBuilder().token('5116521471:AAGyvwDZw-yFq7R_Pl5YDRHid77P4DwBu6Y').build()

    start_handler = CommandHandler('start', start)
    # set_timer = CommandHandler('set_timer', set_date)
    timer = ConversationHandler(
        entry_points=[CommandHandler('set_timer', set_date)],
        states={
            INPUT_DATE: [MessageHandler(filters.Regex(r"^\s*\d\d\.\d\d\.\d\d\s*\d\d\:\d\d\s*$"), check)]
            # CHOOSE: []
        },
        fallbacks=[CommandHandler('start', start)])
    application.add_handler(start_handler)
    application.add_handler(timer)
    application.run_polling()
