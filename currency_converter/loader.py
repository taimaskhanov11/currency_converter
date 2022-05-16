from aiogram import Bot, Dispatcher
from aiogram.dispatcher.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from currency_converter.config.config import config

logger.info(config.bot.token)
bot = Bot(token=config.bot.token)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
scheduler = AsyncIOScheduler(timezone="Europe/Moscow")


# i18n = setup_lang_middleware(dp)
# _ = i18n.gettext


def _(text):
    return text
