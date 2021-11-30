from bs4 import BeautifulSoup
import requests
from setting import DOMAIN


def pages_available():
    pass


def parse_books_on_page(book_name, page_num=1):
    result = []
    payload = {
        'q': book_name,
    }
    page_num = '' if page_num == 1 else f'pagenum-{page_num}'
    page = requests.get(
        f'{DOMAIN}/pages/rmd_search_arts/{page_num}', params=payload).text
    html = BeautifulSoup(page, "html.parser")
    not_found = html.select_one('div.b_search p')
    if not_found:
        # TODO: inform user in telegram by message
        print('Ничего не найдено по запросу:', book_name)
        return
    books_data = html.find_all(
        "li", attrs={"data-filter-class": "['notread']"})
    for book_data in books_data:
        link_data = book_data.find('a')['href']
        book_author = link_data.split('/')[2]
        book_link = f"{DOMAIN}/{link_data}"
        book_title = book_data.find("p", attrs={"class": "booktitle"}).text
        result.append(
            {
                'title': book_title,
                'author': book_author,
                'link': book_link
            }
        )
    return result
