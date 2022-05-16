from aiogram import Dispatcher, Router, types
from aiogram.dispatcher.fsm.context import FSMContext

from currency_converter.apps.bot import markups
from currency_converter.apps.bot.filters.base_filters import UserFilter, StateClearFilter
from currency_converter.db.models import User

router = Router()


async def start(message: types.Message, user: User, state: FSMContext):
    await state.clear()
    await message.answer("Бот запущен", reply_markup=markups.common_menu.start_menu())


def register_common(dp: Dispatcher):
    dp.include_router(router)

    callback = router.callback_query.register
    message = router.message.register

    message(start, UserFilter(), StateClearFilter(), commands="start", state="*")
