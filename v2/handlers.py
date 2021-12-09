import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram_bot_pagination import InlineKeyboardPaginator
from setting import DOWNLOAD_FAIL_MESSAGE, START_MESSAGE, UNKNOWN_COMMAND_MESSAGE, BOOKS_ON_PAGE, COULDNT_DOWNLOAD_MESSAGE
from utils import parse_book_details, parse_books_on_page, extract_file
from utils import download_file_new_format, download_file_old_format
from telegram import ParseMode
from math import ceil


books = {}
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=START_MESSAGE)


def search_book(update, context):
    global books
    username = update.message.chat.username
    
    book_name = update.message.text
    books[username] = parse_books_on_page(book_name)
    
    if books[username]:
        pages = ceil(len(books[username]) / BOOKS_ON_PAGE)
        paginator = InlineKeyboardPaginator(pages)

        # Separating books on different pages, by the specified quantity
        page, books_counter = 1, 0
        paged_message = {}
        temp_message = f"Найдено: {len(books[username])} книг\n\n"

        for book_id, book in books[username].items():
            temp_message += f"<b>{book['title']}</b>\n{book['author']}\nСкачать книгу: /download{book_id}\n\n"
            books_counter += 1
            
            if books_counter == BOOKS_ON_PAGE:
                paged_message[page] = temp_message
                books_counter = 0
                page += 1
                temp_message = ""
    else:
        paged_message = 'Ничего не найдено'
    
    books[username]["paginator_info"] = paged_message

    context.bot.send_message(
        chat_id=update.effective_chat.id, text=paged_message[1], reply_markup=paginator.markup, parse_mode=ParseMode.HTML)


def download(update, context, book_id):
    global books

    try:
        username = update.message.chat.username

        book_page_link = books[username][book_id]['link']
        book_details = parse_book_details(book_page_link)

        # Adding download links to chosen book
        if not books[username][book_id]["formats"]:
            books[username][book_id]["formats"] = book_details["formats"]

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

    username = update.callback_query.message.chat.username
    page = int(query.data.split()[1])

    try:
        paginator = InlineKeyboardPaginator(
            len(books[username]["paginator_info"]),
            current_page=page,
            data_pattern='{page}'
        )

        page_text = books[username]["paginator_info"][page]
        print(query)
        message_id = query.message.message_id
        context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            text=page_text,
            message_id=message_id,
            reply_markup=paginator.markup,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        print("Pager error:", e)


def downloader_callback(update, context):
    global books

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
        file_link = books[username][book_id]["formats"][format_id]["link"]

        # Checking whether it's a new standard of file link or not
        if "formats" in file_link:
            filename = download_file_new_format(file_link, username)
        else:
            filename = download_file_old_format(file_link, username)

        if "zip" in filename:
            filename = extract_file(filename)
            
        # Sending file
        title = books[username][book_id]["title"]
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

