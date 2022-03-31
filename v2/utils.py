from distutils.command.build import build
import os
import re
from bs4 import BeautifulSoup
import requests
from setting import DOMAIN, TEMP_DIR, BOOKS_ON_DOMAIN_PAGE
from zipfile import ZipFile
from aiogram.types import InlineKeyboardButton

async def parse_books_on_page(book_name, quantity=BOOKS_ON_DOMAIN_PAGE):
    result = {}
    payload = {"q": book_name}
    page = requests.get(f"{DOMAIN}/pages/rmd_search_arts/", params=payload).text
    html = BeautifulSoup(page, "html.parser")

    not_found = html.select_one("div.b_search p")
    if not_found:
        return

    books_data = html.find_all("li", attrs={"data-filter-class": "['notread']"})

    for book_index, book_data in enumerate(books_data[0:quantity]):
        link_data = book_data.find("a")["href"]
        book_title = book_data.select_one("p.booktitle").text
        book_author = link_data.split("/")[2]
        book_link = f"{DOMAIN}{link_data}"
        result[book_index] = {
            "title": book_title,
            "author": book_author,
            "link": book_link,
            "formats": {},
        }

    return result


async def parse_book_details(book_page_link):
    page = requests.get(book_page_link).text
    html = BeautifulSoup(page, "html.parser")

    book_thumb_regex = re.compile('.*cover_type.*')
    book_thumb_link = html.find("span", attrs={"class": book_thumb_regex}).find("img")["src"]
    book_title = html.find("h1", attrs={"data-widget-litres-book": 1}).text
    book_author = html.find("a", attrs={"data-widget-litres-author": 1}).text
    book_annotation = html.find("div", id="book_annotation")
    # Getting rid of garbage that can prevent parsing message
    book_annotation.div.decompose()
    book_annotation = re.sub("<[^>]+>", "", book_annotation.text)

    download_formats = html.find(
        "div", attrs={"class": "item_download item_info border_bottom"}
    ).find_all("a")

    download_links = {}
    html_link = False
    book_trial = False
    for link_index, link in enumerate(download_formats):
        book_format = link.text.split(".")[0]
        book_format_download_link = f"{DOMAIN}{link['href']}"

        # Skipping this type of format due to disability
        if book_format == "html":
            html_link = True
            continue

        download_links[link_index] = {
            "format": book_format,
            "link": book_format_download_link,
        }

    if html_link:
        # Shifting dictionary indexes to the left
        download_links = fix_dict(download_links)

    book_trial = check_trial(download_links[0]["link"])

    result = {
        "title": book_title,
        "author": book_author,
        "annotation": book_annotation,
        "formats": download_links,
        "is_trial": book_trial,
        "thumb_link": book_thumb_link,
    }

    return result


def check_trial(download_link):
    if "formats" in download_link:
        return True
    return False


def fix_dict(old_dict):
    new_dict = {}

    for index in old_dict.keys():
        new_dict[index - 1] = old_dict[index]

    return new_dict


def build_keyboard(formats, book_id, keyword, row_width):
    keyboard, row = [], []
    counter = 0

    for format_id, format_info in formats.items():
        row.append(InlineKeyboardButton(format_info["format"], callback_data=f"{keyword} {format_id} {book_id}"))
        counter += 1
        
        # Adding row if row is fully filled or if loop is over
        if counter == row_width or format_id == len(formats) - 1:
            keyboard.append(row)
            row = []
            counter = 0

    return keyboard


async def download_manager(books, user_id, button_data, inline=False):
    # Getting which book format user wants
    *_, format_id, book_id = button_data.split()
    format_id, book_id = int(format_id), int(book_id)

    # Changing user's books storage if query is made from inline mode
    storage = "inline_books" if inline else "books"
    file_link = books[user_id][storage][book_id]["formats"][format_id]["link"]
    book_title = books[user_id][storage][book_id]["title"]

    # Checking whether it's a new standard of link or not
    if "formats" in file_link:
        temp_filename = await download_file_new_format(file_link, user_id)
    else:
        temp_filename = await download_file_old_format(file_link, user_id)

    if "zip" in temp_filename:
        temp_filename = await extract_file(temp_filename)

    return [book_title, temp_filename]

async def download_file_new_format(download_page_link, user_id):
    response = requests.get(download_page_link)
    page = response.text
    html = BeautifulSoup(page, "html.parser")

    temp_filename = TEMP_DIR + str(user_id) + "_" + download_page_link.split("/")[5]

    # Getting file's format from URL
    format = download_page_link.split("/")[-1].split("=")[-1]

    # These formats are incorrect
    if format in ["a4.pdf", "a6.pdf"]:
        format = format.split(".")[0] + ".zip"
    elif format == "fb3":
        format = "zip"

    temp_filename += "." + format

    file_link = html.select_one("div.download_progress_txt a")["href"]
    file = requests.get(file_link).content

    with open(temp_filename, "wb") as f:
        f.write(file)

    return temp_filename


async def download_file_old_format(file_link, user_id):
    temp_filename = TEMP_DIR + str(user_id) + "_" + file_link.split("/")[5]

    # Getting file's format from URL
    format = file_link.split("/")[-1][len("download.") :]

    temp_filename += "." + format

    file = requests.get(file_link).content

    with open(temp_filename, "wb") as f:
        f.write(file)

    return temp_filename


# async def pdf_loader(url, filename):
#     "Download pdf from html preview mode"
#     response = requests.get(url, stream=True)
#     print(response)
#     if response.status_code == 200:
#         with open(filename, 'wb') as pdf_file:
#             for chunk in response.iter_content(chunk_size=1024):
#                 pdf_file.write(chunk)
#     else:
#         print(f"Failed to load pdf: {url}")


async def extract_file(path):
    # Unpacking and delete archive
    with ZipFile(path, "r") as zip_obj:
        temp_filename = TEMP_DIR + zip_obj.namelist()[0]
        zip_obj.extractall(TEMP_DIR)
    os.remove(path)

    return temp_filename
