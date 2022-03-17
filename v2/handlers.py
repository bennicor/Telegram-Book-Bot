import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram_bot_pagination import InlineKeyboardPaginator
from setting import DOWNLOAD_FAIL_MESSAGE, START_MESSAGE, UNKNOWN_COMMAND_MESSAGE, BOOKS_ON_PAGE, COULDNT_DOWNLOAD_MESSAGE
from utils import parse_book_details, parse_books_on_page, extract_file
from utils import download_file_new_format, download_file_old_format
from telegram import ParseMode
from math import ceil


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=START_MESSAGE)


def search_book(update, context):
    book_name = update.message.text
    # Saving query result into local user database
    context.user_data["books"] = parse_books_on_page(book_name)
    context.user_data["prev_page"] = 1

    if context.user_data["books"]:
        books_found = len(context.user_data["books"])
        pages = ceil(books_found / BOOKS_ON_PAGE)
        paginator = InlineKeyboardPaginator(pages)

        # Separating books on different pages by specified quantity
        page, books_counter = 1, 0
        paged_message = {}
        temp_message = f"Найдено: {books_found} книг\n\n"

        for book_id, book in context.user_data["books"].items():
            temp_message += f"<b>{book['title']}</b>\n{book['author']}\nСкачать книгу: /download{book_id}\n\n"
            books_counter += 1
            
            # Display fixed amount of books on page,
            # only if total amount is higher
            if books_counter == BOOKS_ON_PAGE if books_found >= BOOKS_ON_PAGE else books_found: 
                paged_message[page] = temp_message
                books_counter = 0
                page += 1
                temp_message = f"Найдено: {books_found} книг\n\n"

        context.user_data["books"]["paginator_info"] = paged_message

        context.bot.send_message(
            chat_id=update.effective_chat.id, text=paged_message[1], reply_markup=paginator.markup, parse_mode=ParseMode.HTML)
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id, text='Ничего не найдено')


def download(update, context, book_id):
    try:
        book_page_link = context.user_data["books"][book_id]['link']
        book_details = parse_book_details(book_page_link)

        # Adding download links to chosen book
        if not context.user_data["books"][book_id]["formats"]:
            context.user_data["books"][book_id]["formats"] = book_details["formats"]

        if book_details['is_trial']:
            book_details['title'] += '(пробная версия)'

        message = f"<b>{book_details['title']}</b>\n{book_details['author']}\n\n{book_details['annotation']}"

        
        download_keyboard = [list([InlineKeyboardButton(format_info["format"], callback_data=f"download {format_id} {book_id}") for format_id, format_info in book_details["formats"].items()])]

        reply_markup = InlineKeyboardMarkup(download_keyboard)

        context.bot.send_message(
            chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    except Exception as e:
        print("Unable to download book:", e)
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=DOWNLOAD_FAIL_MESSAGE)


def buttons(update, context):
    callback_data = update.callback_query.data
    button_type = callback_data.split()[0]

    if button_type == "download":
        downloader_callback(update, context)
    elif button_type == "pager":
        pager_callback(update, context)


def pager_callback(update, context):
    query = update.callback_query
    query.answer()

    page = int(query.data.split()[1])

    # Checking if user've choosen same page
    if page != context.user_data["prev_page"]:
        context.user_data["prev_page"] = page
        paginator = InlineKeyboardPaginator(
            len(context.user_data["books"]["paginator_info"]),
            current_page=page,
            data_pattern='{page}'
        )

        page_text = context.user_data["books"]["paginator_info"][page]
        message_id = query.message.message_id
        context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            text=page_text,
            message_id=message_id,
            reply_markup=paginator.markup,
            parse_mode=ParseMode.HTML
        )


def downloader_callback(update, context):
    try:
        # Closing buttons
        message_text = update.callback_query.message.text
        message_id = update.callback_query.message.message_id

        context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            text=message_text,
            message_id=message_id,
            reply_markup=InlineKeyboardMarkup([]))

        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Скачиваем книгу...")

        username = update.callback_query.message.chat.username
        query = update.callback_query
        query.answer()
        button_data = query.data

        # Getting which format user wants to get book in
        _, format_id, book_id = button_data.split()
        format_id, book_id = int(format_id), int(book_id)
        file_link = context.user_data["books"][book_id]["formats"][format_id]["link"]
        print(file_link)

        # Checking whether it's a new standard of file link or not
        if "formats" in file_link:
            filename = download_file_new_format(file_link, username)
        else:
            filename = download_file_old_format(file_link, username)

        if "zip" in filename:
            filename = extract_file(filename)
            
        # Sending file
        title = context.user_data["books"][book_id]["title"]
        context.bot.send_document(
            chat_id=update.effective_chat.id, document=open(filename, "rb"), caption=title)
            
        # Deleting file after sending
        os.remove(filename)
    except Exception as e:
        print("Unable to download book:", e)


def unknown_command(update, context):
    command = update.message.text
    if "download" in command:
        try:
            book_id = int(command[9:])
            download(update, context, book_id)
        except Exception as e:
            print("Couldn't get book id:", e)
            context.bot.send_message(chat_id=update.effective_chat.id, text=COULDNT_DOWNLOAD_MESSAGE)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text=UNKNOWN_COMMAND_MESSAGE)

