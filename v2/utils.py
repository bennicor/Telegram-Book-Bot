import os
from bs4 import BeautifulSoup
import requests
from transliterate import translit
from setting import DOMAIN, TEMP_DIR
from zipfile import ZipFile


def pages_available():
    pass


def parse_books_on_page(book_name, page_num=1):
    result = {}
    payload = {
        'q': book_name
    }
    page_num = '' if page_num == 1 else f'pagenum-{page_num}'
    page = requests.get(
        f'{DOMAIN}/pages/rmd_search_arts/{page_num}', params=payload).text
    html = BeautifulSoup(page, 'html.parser')

    not_found = html.select_one('div.b_search p')
    if not_found:
        return

    books_data = html.find_all(
        'li', attrs={'data-filter-class': "['notread']"})

    for book_index, book_data in enumerate(books_data):
        link_data = book_data.find('a')['href']
        book_title = book_data.select_one('p.booktitle').text
        book_author = link_data.split('/')[2]
        # book_author = translit_author(book_author)
        book_link = f'{DOMAIN}{link_data}'
        result[book_index] = {
                'title': book_title,
                'author': book_author,
                'link': book_link,
                'formats': ''
            }

    return result


def parse_book_details(book_page_link):
    page = requests.get(book_page_link).text
    html = BeautifulSoup(page, 'html.parser')

    book_title = html.find('h1', attrs={'data-widget-litres-book': 1}).text
    book_author = html.find('a', attrs={'data-widget-litres-author': 1}).text
    book_annotation = html.find('div', id='book_annotation')
    # Getting rid of inner tags
    book_annotation.div.decompose()

    download_formats = html.find('div', attrs={'class': 'item_download item_info border_bottom'})
    download_formats = download_formats.find_all('a')

    download_links = {}
    html_link = book_trial = False
    for link_index, link in enumerate(download_formats):
        book_format = link.text
        book_format_download_link = f"{DOMAIN}{link['href']}"

        # Skipping this type of format
        if book_format == 'html.zip':
            html_link = True
            continue

        download_links[link_index] = {
            'format': book_format,
            'link': book_format_download_link
        }

    if html_link:
        download_links = fixed_dict(download_links)

    book_trial = check_trial(download_links[0]['link'])

    result = {
        'title': book_title,
        'author': book_author,
        'annotation': book_annotation.text,
        'formats': download_links,
        'is_trial': book_trial
    }

    return result


def check_trial(download_link):
    if 'formats' in download_link:
        return True
    return False


def fixed_dict(old_dict):
    new_dict = {}

    for index in old_dict.keys():
        new_dict[index - 1] = old_dict[index]
    
    return new_dict


def translit_author(author):
    # kruteckaya_valentina
    translited_author = " ".join(author.split("_"))
    translited_author = translit(translited_author, "ru").capitalize()

    return translited_author


def download_file_new_format(file_link):
    page = requests.get(file_link).text
    html = BeautifulSoup(page, "html.parser")

    filename = TEMP_DIR + file_link.split("/")[5]
    format = file_link.split("/")[-1].split("=")[-1]

    # These formats are incorrect
    if format in ["a4.pdf", "a6.pdf"]:
        format = format.split(".")
        format[1] = ".zip"
        format = "".join(format)
    elif format == "fb3":
        format = "zip"

    filename += "." + format

    file_link = html.select_one("div.download_progress_txt a")["href"]
    file = requests.get(file_link).content

    with open(filename, "wb") as f:
        f.write(file)

    return filename


def download_file_old_format(file_link):
    filename = TEMP_DIR + file_link.split("/")[5]
    format = file_link.split("/")[-1][len("download."):]
    
    filename += "." + format

    file = requests.get(file_link).content

    with open(filename, "wb") as f:
        f.write(file)

    return filename

def extract_file(path):
    # Unpacking and delete archive
    with ZipFile(path, "r") as zip_obj:
        filename = TEMP_DIR + zip_obj.namelist()[0]
        zip_obj.extractall(TEMP_DIR)
    os.remove(path)

    return filename

if __name__ == '__main__':
    # print(parse_book_details('https://aldebaran.ru/author/goncharov_ivan/kniga_oblomov1859_ru/'))
    # extract_file("3data.zip")
    print(download_file_new_format("https://aldebaran.ru/download/buk_artem/kniga_voyina_sherifa_oblomova/?formats=epub"))