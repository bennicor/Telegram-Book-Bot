import os
from setting import (
    DOWNLOAD_FAIL_MESSAGE,
    START_MESSAGE,
    UNKNOWN_COMMAND_MESSAGE,
    BOOKS_ON_PAGE,
    COULDNT_DOWNLOAD_MESSAGE,
    TOKEN
)
from utils import parse_book_details, parse_books_on_page, extract_file
from utils import download_file_new_format, download_file_old_format
from math import ceil
from telegram_bot_pagination import InlineKeyboardPaginator
from aiogram.types.message import ParseMode
from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Bot
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

# Creating bot instance to handle messages changes
bot = Bot(token=TOKEN)
books = {}  # Global dictionary where all users data is stored


async def start(message):
    chat_id = message.chat.id
    await bot.send_message(text=START_MESSAGE, chat_id=chat_id)


async def search_book(message):
    'Sends back all the books that were found by the users query'
    global books

    user_id = message.from_user.id
    book_name = message.text

    # Saving query results
    books[user_id] = {}
    books[user_id]["books"] = await parse_books_on_page(book_name)
    books[user_id]["prev_page"] = 1

    if books[user_id]["books"]:
        books_found = len(books[user_id]["books"])
        pages = ceil(books_found / BOOKS_ON_PAGE)
        paginator = InlineKeyboardPaginator(pages)

        # Separating books on different pages by specified quantity
        last_page_books_amount = books_found % BOOKS_ON_PAGE
        next_page_requirements = False
        page, books_counter = 1, 0
        paged_message = {}
        temp_message = f"Найдено: {books_found} книг\n\n"

        for book_id, book in books[user_id]["books"].items():
            temp_message += f"<b>{book['title']}</b>\n{book['author']}\nСкачать книгу: /download{book_id}\n\n"
            books_counter += 1

            # Checking if page is filled with certain amount of books
            if books_found >= BOOKS_ON_PAGE:
                if page < pages:
                    next_page_requirements = books_counter == BOOKS_ON_PAGE
                else:
                    next_page_requirements = books_counter == last_page_books_amount
            else:
                next_page_requirements = books_counter == books_found

            if next_page_requirements:
                paged_message[page] = temp_message
                books_counter = 0
                page += 1
                temp_message = f"Найдено: {books_found} книг\n\n"

        books[user_id]["books"]["paginator_info"] = paged_message
        chat_id = message.chat.id

        await bot.send_message(
            chat_id=chat_id,
            text=paged_message[1],
            reply_markup=paginator.markup,
            parse_mode=ParseMode.HTML,
        )
    else:
        await bot.send_message(text="Ничего не найдено", chat_id=chat_id)


async def download(message, book_id):
    '''
    Sends back more concrete information about the book user have choosen
    and provide several downloadihg ways 
    '''
    global books

    try:
        user_id = message.from_user.id
        book_page_link = books[user_id]["books"][book_id]["link"]
        book_details = await parse_book_details(book_page_link)

        # Adding download links to chosen book
        books[user_id]["books"][book_id]["formats"] = book_details["formats"]

        if book_details["is_trial"]:
            book_details["title"] += "(пробная версия)"

        book_info = f"<b>{book_details['title']}</b>\n{book_details['author']}\n\n{book_details['annotation']}"

        download_keyboard = [
            list(
                [
                    InlineKeyboardButton(
                        format_info["format"],
                        callback_data=f"download {format_id} {book_id}",
                    )
                    for format_id, format_info in book_details["formats"].items()
                ]
            )
        ]

        reply_markup = InlineKeyboardMarkup(row_width=3,inline_keyboard=download_keyboard)

        chat_id = message.chat.id

        await bot.send_message(
            chat_id=chat_id, 
            text=book_info,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logging.error("Unable to download book", exc_info=True)
        await bot.send_message(text=DOWNLOAD_FAIL_MESSAGE, chat_id=chat_id)


async def buttons(callback):
    'Gets information about pressed button and redirect to appropriate functions'
    callback_data = callback.data
    button_type = callback_data.split()[0]

    if button_type == "download":
        await downloader_callback(callback)
    elif button_type == "pager":
        await pager_callback(callback)


async def pager_callback(callback):
    'Updates message and paginator statement'
    global books
    
    await callback.answer()

    page = int(callback.data.split()[1])
    user_id = callback.from_user.id

    # Checking if user've choosen same page
    if page == books[user_id]["prev_page"]:
        return

    # Updating paginator keyboard
    books[user_id]["prev_page"] = page
    paginator = InlineKeyboardPaginator(
        len(books[user_id]["books"]["paginator_info"]),  # Number of pages
        current_page=page,
    )

    # Updating page message
    chat_id = callback.message.chat.id
    message_id = callback.message.message_id
    page_text = books[user_id]["books"]["paginator_info"][page]

    await bot.edit_message_text(
        text=page_text,
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=paginator.markup,
        parse_mode=ParseMode.HTML,
    )


async def downloader_callback(callback):
    'Downloads book in required format and sends back to user'
    try:
        chat_id = callback.message.chat.id
        message_id = callback.message.message_id
        message_text = callback.message.text
        user_id = callback.from_user.id

        await bot.edit_message_text(
            chat_id=chat_id,
            text=message_text,
            message_id=message_id,
            reply_markup=InlineKeyboardMarkup([]),  # Closing buttons panel
        )

        await bot.send_message(
            chat_id=chat_id, text="Скачиваем книгу..."
        )

        await callback.answer()
        button_data = callback.data

        # Getting which book format user wants
        _, format_id, book_id = button_data.split()
        format_id, book_id = int(format_id), int(book_id)
        file_link = books[user_id]["books"][book_id]["formats"][format_id]["link"]

        # Checking whether it's a new standard of link or not
        if "formats" in file_link:
            temp_filename = await download_file_new_format(file_link, chat_id)
        else:
            temp_filename = await download_file_old_format(file_link, chat_id)

        if "zip" in temp_filename:
            temp_filename = await extract_file(temp_filename)

        # Sending file
        book_title = books[user_id]["books"][book_id]["title"]
        await bot.send_document(
            chat_id=chat_id,
            document=open(temp_filename, "rb"),
            caption=book_title,
        )

        # Deleting file after sending
        os.remove(temp_filename)
    except Exception as e:
        logging.error("Unable to download book", exc_info=True)


async def command_handler(message):
    command = message.text
    chat_id = message.chat.id
    message_id = message.message_id


    # Checking if command is valid
    if "download" in command:
        try:
            book_id = int(command[len("download") + 1 :])
            await download(message, book_id)
        except Exception as e:
            logging.error("Couldn't get book id", exc_info=True)
            await bot.send_message(text=COULDNT_DOWNLOAD_MESSAGE, chat_id=chat_id, message_id=message_id)
    else:
        await bot.send_message(text=UNKNOWN_COMMAND_MESSAGE, chat_id=chat_id, message_id=message_id)
