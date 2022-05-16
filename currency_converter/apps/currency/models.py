import datetime

from pydantic import BaseModel

from currency_converter.config.config import TZ

"""EUB.KZ USD 430.50 / 432.00 (HH.MM.SS)
Предыдущий курс USD 431.00 / 433.00"""


class Currency(BaseModel):
    title: str
    buying: float
    selling: float

    def __str__(self):
        date = datetime.datetime.now(tz=TZ)
        return f"{self.title} {self.buying} / {self.selling} ({date.hour}.{date.minute}.{date.second})"

    def compare(self, other: 'Currency') -> bool:
        if (self.buying != other.buying) or (self.selling != other.selling):
            return True
        return False
