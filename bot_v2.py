from telegram.ext import Updater
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.filters import Filters
from telegram.ext.messagehandler import MessageHandler

from handlers import search_book, start
from setting import TOKEN


def start_bot():
    try:
        updater = Updater(token=TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(MessageHandler(
            Filters.text & (~Filters.command), search_book))
        updater.start_polling()
        updater.idle()
    except Exception as e:
        print('Failed to start bot:', e)
