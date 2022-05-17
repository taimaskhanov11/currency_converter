import asyncio

import aiohttp
from bs4 import BeautifulSoup, element
from loguru import logger

from currency_converter.apps.currency.models import Currency
from currency_converter.apps.currency.temp import EXCHANGE
from currency_converter.apps.currency.utils import send_message
from currency_converter.config.config import config

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36",
}

eubank_cookies = "sbjs_migrations=1418474375998%3D1; sbjs_first_add=fd%3D2022-05-16%2013%3A30%3A20%7C%7C%7Cep%3Dhttps%3A%2F%2Feubank.kz%2Fexchange-rates%2F%7C%7C%7Crf%3Dhttps%3A%2F%2Fkwork.ru%2F; sbjs_current=typ%3Dreferral%7C%7C%7Csrc%3Dkwork.ru%7C%7C%7Cmdm%3Dreferral%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%2F%7C%7C%7Ctrm%3D%28none%29; sbjs_first=typ%3Dreferral%7C%7C%7Csrc%3Dkwork.ru%7C%7C%7Cmdm%3Dreferral%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%2F%7C%7C%7Ctrm%3D%28none%29; _gcl_au=1.1.52721673.1652697021; _gid=GA1.2.1876166362.1652697021; _ym_uid=1652697021553318343; _ym_d=1652697021; _ym_isad=1; sbjs_current_add=fd%3D2022-05-16%2014%3A22%3A04%7C%7C%7Cep%3Dhttps%3A%2F%2Feubank.kz%2Fexchange-rates%2F%7C%7C%7Crf%3Dhttps%3A%2F%2Fkwork.ru%2F; sbjs_udata=vst%3D2%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F101.0.4951.67%20Safari%2F537.36; _ym_visorc=w; city_id=33; cookies-policy=agree; card_activityId=248b773b-5d4a-4d89-8363-9ff89b009270; _ga_7DJTGHCTQQ=GS1.1.1652700124.2.1.1652701309.60; amp_a96e14=aiJWLUcmYsS5wm56Ju3ulG...1g369l56n.1g36apap8.0.0.0; sbjs_session=pgs%3D5%7C%7C%7Ccpg%3Dhttps%3A%2F%2Feubank.kz%2Fexchange-rates%2F; _ga=GA1.2.1409366310.1652697021"
bcc_cookies = "PHPSESSID=bxBlq4G1QoNPJEgxVqrCCF88CmdK5mOm; BCC_SM_GUEST_ID=25275061; _ga=GA1.2.805220917.1652697017; _gid=GA1.2.1809077959.1652697017; _gcl_au=1.1.2003908492.1652697017; _ym_uid=1652697017571979242; _ym_d=1652697017; BX_USER_ID=e13f66410918f2cf0b171c2aa4a1f517; tmr_lvid=22dd01ebb6d0642c10f7f249d515266e; tmr_lvidTS=1652697017773; _ym_isad=1; c2d_widget_id={%223ef4b8560a2dcd9990c2836502827b8b%22:%22[chat]%2054cc43bb77239004f4bf%22}; BCC_SM_LAST_VISIT=16.05.2022+18%3A31%3A09; tmr_detect=1%7C1652704268791; _ym_visorc=w; tmr_reqNum=27"
# buying and selling
eubank_url = "https://eubank.kz/exchange-rates/"
bcc_url = "https://www.bcc.kz/about/kursy-valyut/"


def parse_eurobank_exchange_rate(text) -> list[dict[str, str | float]]:
    soup = BeautifulSoup(text, "lxml")
    smartbank_table = soup.find_all("div", {"class": "exchanges-tabs-list__item"})[1]
    buying_table, selling_table = smartbank_table.find_all("div", {"class": "exchange__col"})
    buying_body, selling_body = buying_table.find("tbody"), selling_table.find("tbody")
    data = []
    for buy, sell in zip(buying_body.find_all("tr")[:4],
                         selling_body.find_all("tr")[:4]):
        buy: element.Tag
        sell: element.Tag
        title = buy.find("span", {"class": "exchange-table__title"}).text.strip()
        selling = sell.find("span", {"class": "exchange-table__value"}).text.strip()
        buying = sell.find("span", {"class": "exchange-table__value"}).text.strip()
        data.append({
            "title": title,
            "buying": buying,
            "selling": selling,
        })
    return data


def parse_bcc_exchange_rate(text) -> list[dict[str, str | float]]:
    soup = BeautifulSoup(text, "lxml")
    bcc_table = soup.find_all("div", {"class": "s_table_over"})[2]
    bcc_tr_base = bcc_table.find("tbody").find_all("tr")

    bcc_tr_title = bcc_tr_base[0]
    titles_names = [(4, 5), (2, 3), (0, 1)]
    # titles = {
    #     "USD": (0, 1),
    #     "RUB": (2, 3),
    #     "EURO": (4, 5),
    # }
    titles = {}
    for i in bcc_tr_title.find_all("th")[1:]:
        title = i.text.strip()
        titles[title] = titles_names.pop()

    bcc_tr = bcc_tr_base[2]
    tds = list(map(lambda x: x.text.strip(), bcc_tr.find_all("td")[1:]))
    data = []
    for title, value in titles.items():
        data.append({
            "title": title,
            "buying": tds[value[0]],
            "selling": tds[value[1]],
        })

    return data


async def get_eurobank_exchange_rate(session: aiohttp.ClientSession) -> list[dict[str, str | float]]:
    session.headers['Cookie'] = eubank_cookies
    async with session.get(eubank_url) as res:
        return parse_eurobank_exchange_rate(await res.text())


async def get_bcc_exchange_rate(session):
    session.headers["cookie"] = bcc_cookies
    async with session.get(bcc_url) as res:
        return parse_bcc_exchange_rate(await res.text())


async def check_rate(data: list[dict[str, str | float]], bank_info):
    bank = EXCHANGE[bank_info]
    for cur_info in data:
        currency = Currency.parse_obj(cur_info)
        old_currency = bank[currency.title]
        if old_currency.compare(currency):
            text = f"{bank_info}.KZ {currency}\n" \
                   f"Предыдущий курс {old_currency}"
            logger.success(text)
            await send_message(text)
            bank[currency.title] = currency


async def checking_exchange_rate(bank_info):
    async with aiohttp.ClientSession(headers=headers) as session:
        data = await get_eurobank_exchange_rate(session)
        logger.trace(f"{bank_info}|{data}")
        await check_rate(data, bank_info)


async def checking_exchange_rate_start():
    async with aiohttp.ClientSession(headers=headers) as session:
        await send_message(f"Парс EUBANK запущен")
        EXCHANGE["EUBANK"] = {}
        eurobank_currencies = await get_eurobank_exchange_rate(session)
        for cur in eurobank_currencies:
            currency_model = Currency.parse_obj(cur)
            EXCHANGE["EUBANK"][currency_model.title] = currency_model
    try:
        while True:
            logger.debug(f"Проверка EUBANK")
            await checking_exchange_rate("EUBANK")
            await asyncio.sleep(config.bot.interval)
            # scheduler.add_job(checking_exchange_rate, "interval", seconds=config.bot.interval, args=["EUBANK"])
    except Exception as e:
        logger.critical(e)
        await asyncio.sleep(10)


if __name__ == '__main__':
    # scheduler.start()
    loop = asyncio.get_event_loop()
    loop.create_task(checking_exchange_rate_start())
    loop.run_forever()
    # asyncio.run(checking_exchange_rate_start())
