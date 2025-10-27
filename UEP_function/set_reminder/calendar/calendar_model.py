# calendar_model.py
import calendar, datetime
from dataclasses import dataclass

@dataclass
class MonthCell:
    date: datetime.date | None
    in_month: bool

class CalendarModel:
    def __init__(self, year=None, month=None):
        today = datetime.date.today()
        self.year = year or today.year
        self.month = month or today.month
        self.selected_date_iso: str | None = None

    def get_month_matrix(self):
        """
        回傳 6x7 的列表，每個元素是 MonthCell(date_or_None, in_month)
        view 會根據 in_month 來決定樣式與是否可按
        """
        first_weekday, ndays = calendar.monthrange(self.year, self.month) # Mon=0..Sun=6
        matrix = [[MonthCell(None, False) for _ in range(7)] for _ in range(6)]
        day = 1
        row, col = 0, first_weekday
        while day <= ndays:
            matrix[row][col] = MonthCell(datetime.date(self.year, self.month, day), True)
            day += 1
            col += 1
            if col > 6:
                col = 0; row += 1
        return matrix

    def go_prev(self):
        if self.month == 1:
            self.month = 12; self.year -= 1
        else:
            self.month -= 1

    def go_next(self):
        if self.month == 12:
            self.month = 1; self.year += 1
        else:
            self.month += 1
