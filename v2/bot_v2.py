from aiogram import Bot, Dispatcher, executor
from aiogram.dispatcher.filters import Text
from handlers import buttons, search_book, start, command_handler
from setting import TOKEN
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')


def start_bot():
    try:
        bot = Bot(token=TOKEN)
        dispatcher = Dispatcher(bot)

        dispatcher.register_message_handler(start, commands=["start"])
        dispatcher.register_message_handler(command_handler, Text(startswith=["/"]))
        dispatcher.register_message_handler(search_book, content_types="text")
        dispatcher.register_callback_query_handler(buttons)

        asyncio.run(executor.start_polling(dispatcher, skip_updates=True))
    except Exception as e:
        logging.error("Failed to start bot", exc_info=True)
