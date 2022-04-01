from ast import parse
import os
from pydoc import doc
from setting import (
    DOWNLOAD_FAIL_MESSAGE,
    START_MESSAGE,
    UNKNOWN_COMMAND_MESSAGE,
    BOOKS_ON_PAGE,
    GET_BOOK_FAIL_MESSAGE,
    TOKEN,
    INLINE_BOOKS_SEARCH_QUANTITY,
    INLINE_CACHE_TIME,
    INLINE_RAW_WIDTH,
    BOT_STORAGE_CHANNEL_ID,
    CAPTION_LENGTH_LOCK,
)
from utils import (
    parse_book_details,
    parse_books_on_page,
    download_manager,
    build_keyboard,
)
from math import ceil
from telegram_bot_pagination import InlineKeyboardPaginator
from aiogram.types.message import ParseMode
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineQueryResultPhoto,
    InputMediaDocument,
)
from aiogram import Bot
import logging


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(message)s", datefmt="%d-%b-%y %H:%M:%S"
)

# Creating bot instance to handle messages changes
bot = Bot(token=TOKEN)
books = {}  # Global dictionary where all users data is stored



async def start(message):
    chat_id = message.chat.id
    await bot.send_message(text=START_MESSAGE, chat_id=chat_id)


async def search_book(message):
    "Sends back all the books that were found by the users query"
    global books

    chat_id = message.chat.id
    user_id = message.from_user.id
    book_name = message.text

    # Saving query results
    books.setdefault(user_id, {})
    books[user_id]["books"] = await parse_books_on_page(book_name)
    books[user_id]["prev_page"] = 1

    if books[user_id]["books"]:
        books_found = len(books[user_id]["books"])
        pages_amount = ceil(books_found / BOOKS_ON_PAGE)
        paginator = InlineKeyboardPaginator(pages_amount)

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
            if books_found > BOOKS_ON_PAGE:
                if page < pages_amount:
                    next_page_requirements = books_counter == BOOKS_ON_PAGE
                else:
                    # If last page contains less than specified amount per page
                    if last_page_books_amount > 0:
                        next_page_requirements = books_counter == last_page_books_amount
                    else:
                        next_page_requirements = books_counter == BOOKS_ON_PAGE
            else:
                next_page_requirements = books_counter == books_found

            if next_page_requirements:
                paged_message[page] = temp_message
                books_counter = 0
                page += 1
                temp_message = f"Найдено: {books_found} книг\n\n"

        books[user_id]["books"]["paginator_info"] = paged_message

        await bot.send_message(
            chat_id=chat_id,
            text=paged_message[1],
            reply_markup=paginator.markup,
            parse_mode=ParseMode.HTML,
        )
    else:
        await bot.send_message(text="Ничего не найдено", chat_id=chat_id)


async def download(message, book_id): 
    """
    Sends back more concrete information about the book user have choosen
    and provide several downloadihg ways
    """
    global books

    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        book_page_link = books[user_id]["books"][book_id]["link"]
        book_details = await parse_book_details(book_page_link)

        # Adding download links to chosen book
        books[user_id]["books"][book_id]["formats"] = book_details["formats"]

        if book_details["is_trial"]:
            book_details["title"] += "(пробная версия)"

        book_info = f"<b>{book_details['title']}</b>\n{book_details['author']}\n\n{book_details['annotation']}"

        download_keyboard = build_keyboard(book_details["formats"], book_id, "download", INLINE_RAW_WIDTH)
        reply_markup = InlineKeyboardMarkup(inline_keyboard=download_keyboard)

        # Caption length must in range of 0-1024 symbols
        if len(book_info) > CAPTION_LENGTH_LOCK:
            book_info = book_info[:CAPTION_LENGTH_LOCK - 3] + "..."

        await bot.send_photo(
            chat_id=chat_id,
            photo=book_details["thumb_link"],
            caption=book_info,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        chat_id = message.chat.id
        logging.error("Unable to download book", exc_info=True)
        await bot.send_message(text=GET_BOOK_FAIL_MESSAGE, chat_id=chat_id)


async def inline_download(inline_query):
    global books

    book_name = inline_query.query or "" # Getting book title from inline command input
    user_id = inline_query.from_user.id

    # Saving query results
    books.setdefault(user_id, {})
    books[user_id]["inline_books"] = await parse_books_on_page(
        book_name, INLINE_BOOKS_SEARCH_QUANTITY
    )

    if books[user_id]["inline_books"]:
        # Creating a list of all books found
        result = []
        for book_id, book in books[user_id]["inline_books"].items():
            book_name = str(book["title"])

            # Creating a description and inline keyboard for the book
            book_page_link = books[user_id]["inline_books"][book_id]["link"]
            book_details = await parse_book_details(book_page_link)
            books[user_id]["inline_books"][book_id]["formats"] = book_details["formats"]

            if book_details["is_trial"]:
                book_details["title"] += "(пробная версия)"

            book_info = f"<b>{book_details['title']}</b>\n{book_details['author']}\n\n{book_details['annotation']}"

            # Caption length must in range of 0-1024 symbols
            if len(book_info) > CAPTION_LENGTH_LOCK:
                book_info = book_info[:CAPTION_LENGTH_LOCK - 3] + "..."

            download_keyboard = build_keyboard(book_details["formats"], book_id, "inline", INLINE_RAW_WIDTH)
            reply_markup = InlineKeyboardMarkup(inline_keyboard=download_keyboard)

            # A unique id for an inline item
            item = InlineQueryResultPhoto(
                id=book_id,
                title=book_name,
                caption=book_info,
                parse_mode=ParseMode.HTML,
                photo_url=book_details["thumb_link"],
                thumb_url=book_details["thumb_link"],
                photo_width=480,
                photo_height=640,
                reply_markup=reply_markup,
            )

            result.append(item)

        await bot.answer_inline_query(inline_query.id, results=result, cache_time=INLINE_CACHE_TIME)


async def buttons(callback):
    "Gets information about pressed button and redirect to appropriate functions"
    callback_data = callback.data
    button_type = callback_data.split()[0]

    if button_type == "download":
        await downloader_callback(callback)
    elif button_type == "inline":
        await inline_downloader_callback(callback)
    elif button_type == "pager":
        await pager_callback(callback)


async def pager_callback(callback):
    "Updates message and paginator statement"
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
    "Downloads book in required format and sends back to user"
    try:
        global books

        chat_id = callback.message.chat.id
        message_id = callback.message.message_id
        message_text = callback.message.caption
        user_id = callback.from_user.id

        await bot.edit_message_caption(
            chat_id=chat_id,
            message_id=message_id,
            caption=message_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([]),  # Closing buttons panel
        )

        await bot.send_message(chat_id=chat_id, text="Скачиваем книгу...")

        await callback.answer()
        button_data = callback.data

        # Downloading book and getting a file location
        book_title, temp_filename = await download_manager(books, user_id, button_data, inline=False)

        # Sending file
        await bot.send_document(
            chat_id=chat_id,
            document=open(temp_filename, "rb"),
            caption=book_title,
        )

        # Deleting file after sending
        os.remove(temp_filename)
    except Exception as e:
        chat_id = callback.message.chat.id
        logging.error("Unable to download book", exc_info=True)
        await bot.send_message(text=DOWNLOAD_FAIL_MESSAGE, chat_id=chat_id)


async def inline_downloader_callback(callback):
    "Downloads book in required format and sends back to user. Optimized for inline mode"
    try:
        global books

        inline_message_id = callback.inline_message_id
        user_id = callback.from_user.id

        await callback.answer()
        button_data = callback.data

        # Downloading book and getting a file location
        book_title, temp_filename = await download_manager(books, user_id, button_data, inline=True)

        # Sending file to private group to cache file
        # and get access to it later via file_id
        infodoc = await bot.send_document(
            chat_id=BOT_STORAGE_CHANNEL_ID,
            document=open(temp_filename, "rb"),
            caption=book_title,
        )
        
        document_file_id = infodoc["document"]["file_id"]
        media = InputMediaDocument(media=document_file_id, caption=book_title)
        
        # Attaching book to the message
        await bot.edit_message_media(
            inline_message_id=inline_message_id,
            media=media,
            reply_markup=InlineKeyboardMarkup([]), # Closing keyboard
        )

        # Deleting file after sending
        os.remove(temp_filename)
    except Exception as e:
        logging.error("Unable to download book", exc_info=True)
        await bot.edit_message_text(
            inline_message_id=inline_message_id,
            text=DOWNLOAD_FAIL_MESSAGE,
            reply_markup=InlineKeyboardMarkup([]), # Closing keyboard
        )


async def command_handler(message):
    command = message.text
    chat_id = message.chat.id

    # Checking if command is valid
    if "download" in command:
        try:
            book_id = int(command[len("download") + 1 :])
            await download(message, book_id)
        except Exception as e:
            logging.error("Couldn't get book id", exc_info=True)
            await bot.send_message(
                text=GET_BOOK_FAIL_MESSAGE, chat_id=chat_id
            )
    else:
        await bot.send_message(
            text=UNKNOWN_COMMAND_MESSAGE, chat_id=chat_id
        )
