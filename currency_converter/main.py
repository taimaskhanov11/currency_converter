import asyncio
import logging
from threading import Thread

from currency_converter.apps.currency import temp
from currency_converter.apps.currency.async_parser import checking_exchange_rate_start
from currency_converter.apps.currency.parser import Parser
from currency_converter.config.logg_settings import init_logging


async def start():
    # Настройка логирования
    init_logging(
        old_logger=True,
        level="TRACE",
        # old_level=logging.DEBUG,
        old_level=logging.INFO,
        steaming=True,
        write=True,
    )
    # scheduler.start()
    temp.MAIN_LOOP = asyncio.get_event_loop()
    temp.MAIN_LOOP.create_task(checking_exchange_rate_start())
    # await asyncio.sleep(1)
    Thread(target=Parser().start).start()

    # temp.MAIN_LOOP.create_task(asyncio.to_thread(Parser().start()))


def main():
    # asyncio.run(start())
    loop = asyncio.get_event_loop()
    loop.create_task(start())
    loop.run_forever()


if __name__ == "__main__":
    main()
