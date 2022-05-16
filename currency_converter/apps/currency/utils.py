from currency_converter.config.config import config
from currency_converter.loader import bot


async def send_message(text):
    for user_id in config.bot.admins:
        await bot.send_message(user_id, text)
