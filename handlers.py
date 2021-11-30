from utils import parse_books_on_page
from telegram import ParseMode


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='Для начала работы введите название книги или имя автора')


def search_book(update, context):
    username = update.message.chat.username
    books_data = parse_books_on_page(update.message.text)
    if books_data:
        message = f"Найдено: {len(books_data)} книг\n\n"
        for book in books_data:
            message += f"<b>{book['title']}</b>\nСкачать книгу: /download\n\n"
    else:
        message = 'Ничего не найдено'
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.HTML)
