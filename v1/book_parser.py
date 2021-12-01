from bs4 import BeautifulSoup
import requests
from v1.helpers import fix_dict_order


def get_book(book):
    """Searching for all books that matches request"""

    # Get search page content
    # TODO: move 'domain' to upper level
    domain = "https://aldebaran.ru"
    search_URI = f"{domain}/pages/rmd_search_arts/"
    payload = {"q": book}
    page = requests.get(search_URI, params=payload).text
    bpage = BeautifulSoup(page, "html.parser")

    # Check if anything were found
    not_found = bpage.find_all(
        "p", string="В результате поиска ничего не найдено")

    if not_found:
        return

    # Find all matches
    matches = bpage.find_all("li", attrs={"data-filter-class": "['notread']"})

    # TODO: suggestion - try to use walrus operator
    result = {}
    # TODO: rename 'book' variable
    for i, book in enumerate(matches):
        address = book.find("a")["href"]
        title = book.find("p", attrs={"class": "booktitle"}).text

        link = domain + address
        # book_details = get_more(link)

        result[i] = {'title': title, 'link': link}

    return result

# Disabled due to inefficiency


def get_more(link):
    """Return more detailed information on book"""

    domain = "https://aldebaran.ru"
    page = requests.get(link).text
    bpage = BeautifulSoup(page, "html.parser")

    title = bpage.find("h1", attrs={"data-widget-litres-book": 1}).text
    author = bpage.find("a", attrs={"data-widget-litres-author": 1}).text
    annotation = bpage.find("div", id="book_annotation")
    annotation.div.decompose()

    # Getting download links in all available formats, except html one(ain't working)
    formats = bpage.find(
        "div", attrs={"class": "item_download item_info border_bottom"})
    formats_links = formats.find_all("a")

    download, html = {}, False
    for i, link in enumerate(formats_links):
        format = link.text  # TODO: rename the variable
        format_link = domain + link["href"]

        if "html" in format:
            html = True
            continue

        download[i] = [format, format_link]

    # Fixing elements order
    if html:
        fixed_download = fix_dict_order(download)
        del download

    result = [title, author, annotation.text,
              fixed_download if html else download]
    return result


if __name__ == "__main__":
    # get_book("обломов")
    get_more(
        "https://aldebaran.ru/author/vitalius_vasiliyi/kniga_istorii_seksualnyih_oblomov/")
