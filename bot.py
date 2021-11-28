from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, CallbackQueryHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup, File
import logging
from book_parser import get_book, get_more
from helpers import download_file_new

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

# Setting up bot
updater = Updater(token="692790005:AAFTMUA9CEuC51lzmmJenGDJiPdtIRjanNo", use_context=True)
dispatcher = updater.dispatcher

books = {}

# Defining callback functions for handlers
def start(update, context):
    # context.bot.send_message(chat_id=update.effective_chat.id, text="Введите название желаемой книги или автора.")
    context.bot.send_document(chat_id=update.effective_chat.id, document=open("60411026.epub", "rb"), caption="test")

# def inline_caps(update, context):
#     query = update.inline_query.query

#     if not query:
#         return

#     results = []
#     results.append(InlineQueryResultArticle(
#             id=query.upper(),
#             title='Caps',
#             input_message_content=InputTextMessageContent(query.upper())
#     ))

#     context.bot.answer_inline_query(update.inline_query.id, results)

def search_book(update, context):
    global books
    # Each separate user has it's own book list
    username = update.message.chat.username
    books[username] = get_book(update.message.text)

    if not books[username]:
        message = "*Ничего не найдено*"
    else:
        message = f"Найдено: {len(books[username])} книг\n\n"

        for book_id, book in books[username].items():
            message += f"<b>{book[0]}</b>\nСкачать книгу: /download{book_id}\n\n"

    context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.HTML)

def download(update, context, book_id):
    global books
    username = update.message.chat.username

    try:
        link = books[username][book_id][1]
        details = get_more(link)

        # Adding download links to global database variable to access it later
        if len(books[username][book_id]) == 2:
            books[username][book_id].append(details[3])

        # Preparing downlaod message
        message = f"<b>{details[0]}</b>\n{details[1]}\n\n{details[2]}"

        download_keyboard = [
            list([InlineKeyboardButton(format[1][0], callback_data=f"{format[0]} {book_id}") for format in details[3].items()])
        ]

        reply_markup = InlineKeyboardMarkup(download_keyboard)

        context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    except Exception:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Книга не найдена")

def button(update, context):
    global books
    username = update.callback_query.message.chat.username

    query = update.callback_query
    query.answer()
    data = query.data

    # Getting which format user wants to get book in
    format_id, book_id = data.split()
    format_id, book_id = int(format_id), int(book_id)
    file_link = books[username][book_id][2][format_id][1]

    # # Checking whether it's a new standard of file link or not
    if "formats" in file_link:
        filename = download_file_new(file_link)

    # Sending file
    title = books[username][book_id][0]
    context.bot.send_document(chat_id=update.effective_chat.id, document=open(filename, "rb"), caption=title)

def unknown(update, context):
    command = update.message.text
    
    if "download" in command:
        try:
            book_id = int(command[1 + len("download"):len(command)])
            download(update, context, book_id)
        except Exception:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Извините, я не смог распознать введенную команду.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Извините, я не смог распознать введенную команду.")

# Adding commands and messages handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CallbackQueryHandler(button))
dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), search_book))
dispatcher.add_handler(MessageHandler(Filters.command, unknown))

# inline_caps_handler = InlineQueryHandler(inline_caps)
# dispatcher.add_handler(inline_caps_handler)

# Starts bot
updater.start_polling()

# Handles exiting
updater.idle()
