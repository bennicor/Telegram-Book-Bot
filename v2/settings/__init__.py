from pathlib import Path


class Settings:
    def __init__(self):
        self.DOMAIN = "https://aldebaran.ru"
        self.TOKEN = "692790005:AAFTMUA9CEuC51lzmmJenGDJiPdtIRjanNo"
        self.START_MESSAGE = "Для начала работы введите название книги или имя автора"
        self.UNKNOWN_COMMAND_MESSAGE = "Я не смог распознать введенную команду"
        self.GET_BOOK_FAIL_MESSAGE = "Не удалось получить информацию о книге"
        self.DOWNLOAD_FAIL_MESSAGE = "Не удалось скачать книгу"
        self.TEMP_DIR = "v2\\temp"
        self.PROXY_DIR = "v2\\settings\\proxies.txt"
        self.PROXY = []
        self.BOOKS_ON_PAGE = 6
        self.INLINE_BOOKS_SEARCH_QUANTITY = 5
        self.BOOKS_ON_DOMAIN_PAGE = 20
        self.INLINE_CACHE_TIME = 300
        self.INLINE_RAW_WIDTH = 3
        self.BOT_STORAGE_CHANNEL_ID = -1001697530176
        self.CAPTION_LENGTH_LOCK = 1024  # Must be in range (0-1024)

        # Import all proxies from provided list
        # Free proxy, may be obsolete in a few weeks
        proxy_file = str(Path(Path.cwd(), self.PROXY_DIR))

        with open(proxy_file, "r") as proxies:
            for proxy in proxies:
                address, port = proxy.strip().split(":")
                self.PROXY.append(f"{address}:{port}")

        self.HEADERS = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/self.signed-exchange;v=b3;q=0.9",
        }
