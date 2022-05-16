from currency_converter.apps.bot.markups.utils import get_inline_keyboard
from currency_converter.loader import _


def start_menu():
    keyboard = [
        ((_("👤 Мой профиль"), "profile"),),
    ]
    return get_inline_keyboard(keyboard)
