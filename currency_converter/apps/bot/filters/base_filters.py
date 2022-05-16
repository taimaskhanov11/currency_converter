from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from loguru import logger

from currency_converter.db.models import User


class UserFilter(BoundFilter):
    async def check(self, call: types.CallbackQuery, *args, **kwargs) -> dict[str, User]:
        logger.trace(f"{call=}")
        user = call.from_user
        user, is_new = await User.get_or_create(
            user_id=user.id,
            defaults={
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "language": user.language_code,
            },
        )
        if is_new:
            logger.info(f"Новый пользователь {user=}")
        # if user.user_id in config.bot.block_list:
        #     logger.warning(f"{user.user_id} заблокирован")
        #     return False
        return {"user": user}
