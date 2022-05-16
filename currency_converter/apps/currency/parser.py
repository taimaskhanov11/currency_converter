import asyncio
import json
from pathlib import Path
from time import sleep

from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager

from currency_converter.apps.currency import temp
from currency_converter.apps.currency.async_parser import parse_bcc_exchange_rate
from currency_converter.apps.currency.models import Currency
from currency_converter.apps.currency.temp import EXCHANGE
from currency_converter.apps.currency.utils import send_message
from currency_converter.config.config import LOG_DIR, BASE_DIR, config


class by:
    id = "id"
    xpath = "xpath"
    link_text = "link text"
    partial_link_text = "partial link text"
    name = "name"
    tag_name = "tag name"
    class_name = "class name"
    css_selector = "css selector"


class PatchedWebElement(WebElement):
    def fe(self, by=by.id, value=None) -> 'PatchedWebElement':
        pass

    def fes(self, by=by.id, value=None) -> list['PatchedWebElement']:
        pass


class Parser:
    def __init__(self):
        driver_path = ChromeDriverManager().install()
        service = Service(
            driver_path, log_path=str(Path(LOG_DIR, "chrome.log"))
        )
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--headless")
        self.br = webdriver.Chrome(
            service=service,
            options=options,
        )
        self.br.implicitly_wait(2)
        self.br.delete_all_cookies()
        self.repeat = False
        self.url_eubank = "https://eubank.kz/exchange-rates/"
        self.url_bcc = "https://www.bcc.kz/about/kursy-valyut/"
        self._cookie_file = BASE_DIR / "cookies.json"

    def __enter__(self):
        logger.info(f"Opening browser")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.info(f"Closing browser")
        self._save_cookies()
        # sleep(200)
        self.br.quit()

    def _load_cookies(self):
        if self._cookie_file.exists():
            logger.debug("Loading cookies")
            with open(self._cookie_file, "r") as f:
                cookies: list = json.load(f)
                for cookie in cookies:
                    self.br.add_cookie(cookie)
        else:
            logger.debug("Cookie file not found")

    def _save_cookies(self):
        cookies = self.br.get_cookies()
        if cookies:
            logger.debug("Saving cookies")
            with open(self._cookie_file, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2)
        else:
            logger.debug(f"Not have cookies")

    def fe(self, by=by.id, value=None) -> PatchedWebElement:
        element = self.br.find_element(by, value)
        element.fe = element.find_element
        element.fes = element.find_elements
        return element

    def fes(self, by=by.id, value=None) -> list[PatchedWebElement]:
        elements = self.br.find_elements(by, value)
        for elem in elements:
            elem.fe = elem.find_element
            elem.fes = elem.find_elements
        return elements

    def switch_to(self, handler: int):
        self.br.switch_to.window(self.br.window_handles[handler])

    def get(self, url):
        self.br.get(url)

    def send_message(self, text):
        asyncio.run_coroutine_threadsafe(
            send_message(text),
            temp.MAIN_LOOP
        )

    def check_rate(self, data: list[dict[str, str | float]], bank_info):
        bank = EXCHANGE[bank_info]
        for cur_info in data:
            currency = Currency.parse_obj(cur_info)
            old_currency = bank[currency.title]
            if old_currency.compare(currency):
                text = f"{bank_info}.KZ {currency}\n" \
                       f"Предыдущий курс {old_currency}"
                logger.success(text)
                self.send_message(text)
                bank[currency.title] = currency

    def start(self):
        with self:
            self.send_message(f"Парс BCC запущен")
            logger.debug(f"BCC запущен")
            self.get(self.url_bcc)
            EXCHANGE["BCC"] = {}
            sleep(1)
            bcc_currencies = parse_bcc_exchange_rate(self.br.page_source)
            for cur in bcc_currencies:
                currency_model = Currency.parse_obj(cur)
                EXCHANGE["BCC"][currency_model.title] = currency_model
            # self.br.set_page_load_timeout(3)
            while True:
                logger.debug(f"Проверка BCC")
                data = parse_bcc_exchange_rate(self.br.page_source)
                logger.trace(f'BCC|{data}')
                self.check_rate(data, "BCC")
                self.br.refresh()
                sleep(3)
                self.br.execute_script("window.stop();")
                sleep(config.bot.interval)


def main():
    loop = asyncio.get_event_loop()
    temp.MAIN_LOOP = loop
    loop.create_task(asyncio.to_thread(Parser().start()))
    loop.run_forever()
    # print(asyncio.get_event_loop())
    # send_fut = asyncio.run_coroutine_threadsafe(
    #     checking_exchange_rate(),
    #     asyncio.get_event_loop()
    # )
    # send_fut.result()


if __name__ == '__main__':
    main()
