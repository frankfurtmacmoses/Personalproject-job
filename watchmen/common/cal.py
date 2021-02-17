"""
common/cal.py
"""
from datetime import date, timedelta, datetime
from dateutil.easter import easter
import holidays

from watchmen.config import get_boolean, settings
from watchmen.utils.logger import get_logger

LOGGER = get_logger('watchmen.' + __name__)

ADD_HOLIDAY_ERROR = "Holiday cannot be added!"
DATE_ERROR = "Incorrect date formatting!"
DATE_TYPE_ERROR = "The date entered is not of type date. Cannot generate desired information."
REMOVE_HOLIDAY_ERROR = "Holiday cannot be removed!"
WORK_HOUR_TYPE_ERROR = "Work hour must be type int!"

HOLIDAY_GOOD_FRIDAY = get_boolean('holiday.good_friday')
HOLIDAY_BEFORE_XMAS_EVE = get_boolean('holiday.day_before_xmas_eve')
HOLIDAY_THURSDAY_BEFORE_INDEPENDENCE_DAY = get_boolean('holiday.thursday_before_independence_day')
HOLIDAY_FRIDAY_BEFORE_INDEPENDENCE_DAY = get_boolean('holiday.friday_before_independence_day')
HOLIDAY_SPRING_BREAK_DAY = get_boolean('holiday.spring_break_day_bool')

DOW = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

NOM = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


class InfobloxCalendar(object):
    """
    Calendar class containing a list of all Infoblox holidays and ways to query the list.
    NOTE: Holidays need to be updated once a year
    """

    def __init__(self, start=date.today().year, end=None):
        """
        Constructor for watchmen.common.cal.py
        @param start: starting year to generate holidays
        @param end: exclusive ending year to generate holidays
        @note
        There are 3 different constructors:
            1) InfobloxCalendar()
                - This creates a calendar of holidays for the current year
            2) InfobloxCalendar(2021)
                - This creates a calendar for just the given year
            3) InfobloxCalendar(2021, 2090)
                - This creates a calendar for the given range of years (end year exclusive)
        """
        if not isinstance(start, int) or start < 2000 or start > 2100:
            start = date.today().year

        if not isinstance(end, int) or end < start or end > 2100:
            end = start + 1

        self.year_range = list(range(start, end))

        self.holiday_list = holidays.US(state='WA', years=self.year_range, expand=False)
        # Customize holiday list to reflect infoblox holidays
        self._generate_infoblox_holidays()

    def add_holiday(self, year, month, day, name='Custom Infoblox Holiday'):
        """
        Add a custom holiday to the holiday list
        @param year: of new holiday
        @param month: of new holiday
        @param day: of new holiday
        @param name: of new holiday
        @return: An exception if date attributes are None
        @note if the year of the holiday is outside of the range,
        the calendar will populate all the holidays for that year.
        """
        try:
            new_date = '{}-{}-{}'.format(year, month, day)
            self.holiday_list.append({new_date: name})
        except Exception:
            message = "{}\nTrying to add holiday: Year-{} Month-{} Day-{}".format(ADD_HOLIDAY_ERROR, year, month, day)
            LOGGER.error(message)

    def _add_holiday_after_thanksgiving(self):
        """
        Add the day after Thanksgiving to the holiday list
        """
        for key, value in dict(self.holiday_list).items():
            if value == "Thanksgiving":
                next_day = key + timedelta(days=1)
                self.add_holiday(next_day.year, next_day.month, next_day.day, "Day After Thanksgiving (Black Friday)")
                return next_day

    def _add_holiday_before_xmas_eve(self):
        """
        Add the Day before Christmas Eve to the holiday list
        """
        for key, value in dict(self.holiday_list).items():
            if value == "Christmas Eve":
                if key.weekday == 6:
                    day_before = key - timedelta(days=2)
                else:
                    day_before = key - timedelta(days=1)
                self.add_holiday(day_before.year, day_before.month, day_before.day, "Day Before Christmas Eve")
                return day_before

    def _add_holiday_good_friday(self):
        """
        Add Good Friday to the holiday list
        @return:
        """
        for year in self.year_range:
            good_friday = easter(year) - timedelta(days=2)
            self.add_holiday(good_friday.year, good_friday.month, good_friday.day, "Good Friday")

    def _add_holiday_slowdown(self):
        """
        Add the Holiday Slowdown to the holiday list.
        Holiday Slowdown are the following dates: Dec. 26th-31st
        """
        for year in self.year_range:
            day_num = 26
            while day_num <= 31:
                self.add_holiday(year, 12, day_num, "Holiday Slowdown")
                day_num += 1

    def _add_holiday_thursday_before_independence_day(self):
        """
        Add the Thursday before Independence day to the holiday list. This holiday only occurs when Independence day
        falls on a Saturday.
        """
        for key, value in dict(self.holiday_list).items():
            if value == "Independence Day":
                thursday = key - timedelta(days=2)
                self.add_holiday(thursday.year, thursday.month, thursday.day, "Thursday Before Independence Day")

    def _add_holiday_friday_before_independence_day(self):
        """
        Add the Friday before Independence day to the holiday list. This holiday only occurs when Independence day
        falls on a Monday.
        """
        for key, value in dict(self.holiday_list).items():
            if value == "Independence Day":
                friday = key - timedelta(days=3)
                self.add_holiday(friday.year, friday.month, friday.day, "Friday Before Independence Day")

    def _add_holiday_xmas_eve(self):
        """
        Add Christmas Eve to holiday list
        """
        for key, value in dict(self.holiday_list).items():
            if value == "Christmas Day":
                eve = key - timedelta(days=1)
                self.add_holiday(eve.year, eve.month, eve.day, "Christmas Eve")
                return eve

    def _add_holiday_spring_break_day(self):
        """
        Add Spring Break Day to holiday list
        """
        for year in self.year_range:
            day_num = settings('holiday.spring_break_day')
            month_num = settings('holiday.spring_break_month')
            self.add_holiday(year, month_num, day_num, "Spring Break Day")

    @staticmethod
    def _find_weekday(date_to_check):
        """
        Finds which day of the week the given date is
        @param date_to_check:
        @return: int value corresponding with the correct day of the week
        """
        if not isinstance(date_to_check, date):
            LOGGER.error(DATE_TYPE_ERROR)
            return
        return DOW[date_to_check.weekday()]

    def _generate_infoblox_holidays(self):
        """
        Populates holiday list with Infoblox specific holidays and removes holidays that are not days off
        ADD: Day after Thanksgiving, Friday before Independence day, Christmas Eve, Spring Break day and Holiday
        Slowdown (week of Christmas).
        REMOVE: Veteran's Day and Columbus Day
        DEPENDENT: Good Friday and the Day before Christmas Eve
        @note Some years, Good Friday is not an Infoblox holiday
        """
        not_holidays = ["Veterans Day", "Columbus Day"]

        # remove holidays that are still work days
        self.remove_holiday(names=not_holidays)

        # add infoblox specific holidays
        if HOLIDAY_GOOD_FRIDAY:
            self._add_holiday_good_friday()
        if HOLIDAY_THURSDAY_BEFORE_INDEPENDENCE_DAY:
            self._add_holiday_thursday_before_independence_day()
        if HOLIDAY_FRIDAY_BEFORE_INDEPENDENCE_DAY:
            self._add_holiday_friday_before_independence_day()
        self._add_holiday_after_thanksgiving()
        self._add_holiday_slowdown()
        self._add_holiday_xmas_eve()
        if HOLIDAY_BEFORE_XMAS_EVE:
            self._add_holiday_before_xmas_eve()
        if HOLIDAY_SPRING_BREAK_DAY:
            self._add_holiday_spring_break_day()

    def _get_month(self, date_to_check):
        """
        Get the numeric value of the month for a given date
        @param date_to_check:
        @return: the numeric month
        """
        if not isinstance(date_to_check, date):
            LOGGER.error(DATE_TYPE_ERROR)
            return None

        return NOM.get(date_to_check.month)

    def _is_weekend(self, day):
        """
        Determines if given day is a weekend day based on its weekday number.
        5 and 6 represent Saturday and Sunday. 0-4 are Mon-Fri.
        @param day: to be checked
        @return: whether or not the given day is a weekend day or not
        """
        return not day.weekday() < 5

    def is_workday(self, year=date.today().year, month=date.today().month, day=date.today().day):
        """
        Determines if the given day is a work day
        @param year: given year or today's year by default
        @param month: given month or today's month by default
        @param day: given day or today's day by default
        @return: whether or not the given day is a work day
        """
        # has to be input with year-month-day style
        # if not holiday or weekend, return true
        try:
            if year is None and month is None and day is None:
                date_to_check = date.today()
            else:
                date_to_check = date(year, month, day)
        except Exception:
            message = "{}\nTrying to check : Year-{} Month-{} Day-{}".format(DATE_ERROR, year, month, day)
            LOGGER.error(message)
            return None

        not_weekend = not self._is_weekend(date_to_check)
        not_holiday = date_to_check not in self.holiday_list

        return not_weekend and not_holiday

    @staticmethod
    def is_workhour(hour=datetime.now().hour):
        """
        Determines if given hour is between 6am and 6pm; considered work hours
        @param hour: to be checked
        @return: Whether or not the hour falls between 6am and 6pm
        """
        if not isinstance(hour, int):
            LOGGER.error(WORK_HOUR_TYPE_ERROR)
            return False
        return 6 <= hour < 18

    def print_holidays(self):
        """
        Print all the holidays in the list.

        Should print in the order:
            ```
            --------Current Year--------
            Day of the Week, Month Day Year: Name of Holiday
            ```

        Example:
            ```
            --------2020--------
            Wednesday, January 1 2020: New Year's Day
            Monday, February 17 2020: Washington's Birthday
            Friday, April 10 2020: Good Friday
            Monday, May 25 2020: Memorial Day
            ...
            ```
        """
        year = None
        for hol, name in sorted(self.holiday_list.items()):
            day_of_week = InfobloxCalendar._find_weekday(hol)
            month_name = self._get_month(hol)
            if year != hol.year:
                year = hol.year
                print('\n--------{}--------'.format(hol.year))

            print('{}, {} {} {}: {}'.format(day_of_week, month_name, hol.day, hol.year, name))

    def remove_holiday(self, year=None, month=None, day=None, names=None):
        """
        Remove the given date from holiday list or all holidays with the given name(s) from the holiday list
        @param year: of date to be removed
        @param month: of date to be removed
        @param day: of date to be removed
        @param names: single holiday name or list of holiday names that are to be deleted
        """
        if isinstance(names, list):
            for key, value in dict(self.holiday_list).items():
                if value in names:
                    del self.holiday_list[key]
                    LOGGER.info('{} has been removed for {}'.format(value, key.year))
            return

        if isinstance(names, str):
            for key, value in dict(self.holiday_list).items():
                if value == names:
                    del self.holiday_list[key]
            LOGGER.info('{} has been removed for {}'.format(names, key.year))
            return

        try:
            new_date = '{}-{}-{}'.format(year, month, day)
            removed_date = self.holiday_list.pop(new_date)
            LOGGER.info('{} has been removed'.format(removed_date))
        except Exception:
            message = "{}\nTrying to remove holiday: Year-{} Month-{} Day-{}".\
                        format(REMOVE_HOLIDAY_ERROR, year, month, day)
            LOGGER.error(message)
