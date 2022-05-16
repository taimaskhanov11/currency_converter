from typing import Literal

from currency_converter.apps.currency.models import Currency

EXCHANGE: dict[Literal["EUBANK", "BCC"], dict[str, Currency]] = {}
MAIN_LOOP = None
