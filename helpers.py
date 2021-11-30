import requests
from bs4 import BeautifulSoup
from requests.api import request


def fix_dict_order(old_dict):
    fixed_download  = {}
    for i in old_dict.keys():
        fixed_download[i - 1] = old_dict[i]
    
    return fixed_download


def download_file_new_format(file_link):
    page = requests.get(file_link).text
    bpage = BeautifulSoup(page, "html.parser")

    filename = file_link.split("/")[5]
    format = file_link.split("/")[-1]
    format = format.split("=")[-1]

    # These formats are incorrect
    if format in ["a4.pdf", "a6.pdf"]:
        format = format.split(".")
        format[1] = ".zip"
        format = "".join(format)
    elif format == "fb3":
        format = "zip"

    filename += "." + format

    file_link = bpage.find("div", attrs={"class": "download_progress_txt"}).a["href"]
    file = requests.get(file_link).content

    with open(filename, "wb") as f:
        f.write(file)

    return filename

def download_file_old_format(file_link):
    filename = file_link.split("/")[5]
    format = file_link.split("/")[-1][len("download."):]
    
    filename += "." + format

    file = requests.get(file_link).content

    with open(filename, "wb") as f:
        f.write(file)

    return filename

if __name__ == "__main__":
    download_file_new_format("https://aldebaran.ru/download/miller_heminguyeyi_yernest/kniga_starik_i_more_rasskazyi_sbornik/?formats=fb3")
