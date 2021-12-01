import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from setting import DOWNLOAD_FAIL_MESSAGE, START_MESSAGE, UNKNOWN_COMMAND_MESSAGE
from utils import parse_book_details, parse_books_on_page, extract_file
from utils import download_file_new_format, download_file_old_format
from telegram import ParseMode


books = {}
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=START_MESSAGE)


def search_book(update, context):
    global books
    username = update.message.chat.username
    
    books = parse_books_on_page(update.message.text)
    if books:
        message = f"Найдено: {len(books)} книг\n\n"
        for book_id, book in books.items():
            message += f"<b>{book['title']}</b>\n{book['author']}\nСкачать книгу: /download{book_id}\n\n"
    else:
        message = 'Ничего не найдено'
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.HTML)

def download(update, context, book_id):
    global books

    try:
        book_page_link = books[book_id]['link']
        book_details = parse_book_details(book_page_link)

        # Adding download links to chosen book
        if book_details["formats"] != books[book_id]["formats"]:
            books[book_id]["formats"] = book_details["formats"]

        if book_details['is_trial']:
            book_details['title'] += '(пробная версия)'

        message = f"<b>{book_details['title']}</b>\n{book_details['author']}\n\n{book_details['annotation']}"

        download_keyboard = [
            list([InlineKeyboardButton(
                format["format"], callback_data=f"{format_id} {book_id}") for format_id, format in book_details["formats"].items()])
        ]

        reply_markup = InlineKeyboardMarkup(download_keyboard)

        context.bot.send_message(
            chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

    except Exception as e:
        print("Unable to download book:", e)
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=DOWNLOAD_FAIL_MESSAGE)


def button(update, context):
    global books

    query = update.callback_query
    query.answer()
    button_data = query.data

    # Getting which format user wants to get book in
    format_id, book_id = button_data.split()
    format_id, book_id = int(format_id), int(book_id)
    file_link = books[book_id]["formats"][format_id]["link"]

    # Checking whether it's a new standard of file link or not
    if "formats" in file_link:
        filename = download_file_new_format(file_link)
    else:
        filename = download_file_old_format(file_link)

    if "zip" in filename:
        filename = extract_file(filename)
        
    # Sending file
    title = books[book_id]["title"]
    context.bot.send_document(
        chat_id=update.effective_chat.id, document=open(filename, "rb"), caption=title)
        
    # Deleting file after sending
    os.remove(filename)


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

