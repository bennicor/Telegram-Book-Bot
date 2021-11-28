import requests
from bs4 import BeautifulSoup


def fix_dict_order(old_dict):
    fixed_download  = {}
    for i in old_dict.keys():
        fixed_download[i - 1] = old_dict[i]
    
    return fixed_download


def download_file_new(file_link):
    page = requests.get(file_link).text
    bpage = BeautifulSoup(page, "html.parser")

    filename = file_link.split("/")[5]
    format = file_link.split("/")[-1][9:]
    filename += "." + format

    file_link = bpage.find("div", attrs={"class": "download_progress_txt"}).a["href"]
    file = requests.get(file_link).content

    open(filename, "wb").write(file)

    return filename

if __name__ == "__main__":
    download_file_new("https://www.litres.ru/gettrial/?art=22817616&format=epub&&utm_source=aldebaran&utm_medium=referral&utm_campaign=litres&lfrom=192264536")