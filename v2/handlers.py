import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from setting import DOWNLOAD_FAIL_MESSAGE, START_MESSAGE, UNKNOWN_COMMAND_MESSAGE, BOOKS_ON_PAGE
from utils import parse_book_details, parse_books_on_page, extract_file
from utils import download_file_new_format, download_file_old_format
from utils import pages_available
from telegram import ParseMode


books = {}
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=START_MESSAGE)


def search_book(update, context):
    global books
    username = update.message.chat.username
    
    # Getting content from all the pages
    books[username] = {}
    book_name = update.message.text
    book_index = 0
    pages_found = pages_available(book_name)

    for page in range(1, pages_found + 1):
        books[username].update(parse_books_on_page(book_name, page, book_index))
        book_index += BOOKS_ON_PAGE # Increases on amount of books on page
    
    if books[username]:
        message = f"Найдено: {len(books[username])} книг\n\n"
        for book_id, book in books[username].items():
            message += f"<b>{book['title']}</b>\n{book['author']}\nСкачать книгу: /download{book_id}\n\n"
    else:
        message = 'Ничего не найдено'
    
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.HTML)

def download(update, context, book_id):
    global books

    try:
        username = update.message.chat.username

        book_page_link = books[username][book_id]['link']
        book_details = parse_book_details(book_page_link)

        # Adding download links to chosen book
        if not book_details["formats"]:
            books[username][book_id]["formats"] = book_details["formats"]

        if book_details['is_trial']:
            book_details['title'] += '(пробная версия)'

        message = f"<b>{book_details['title']}</b>\n{book_details['author']}\n\n{book_details['annotation']}"

        download_keyboard = [list([InlineKeyboardButton(format["format"].split(".")[0], callback_data=f"{format_id} {book_id}") for format_id, format in book_details["formats"].items()])]

        reply_markup = InlineKeyboardMarkup(download_keyboard)

        context.bot.send_message(
            chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

    except Exception as e:
        print("Unable to download book:", e)
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=DOWNLOAD_FAIL_MESSAGE)


def button(update, context):
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

        username = update.callback_query.message.chat.username
        query = update.callback_query
        query.answer()
        button_data = query.data

        # Getting which format user wants to get book in
        format_id, book_id = button_data.split()
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
            context.bot.send_message(chat_id=update.effective_chat.id, text=UNKNOWN_COMMAND_MESSAGE)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text=UNKNOWN_COMMAND_MESSAGE)

