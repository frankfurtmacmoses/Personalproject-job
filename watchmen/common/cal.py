from datetime import date
import holidays

from watchmen.utils.logger import get_logger

LOGGER = get_logger('watchmen.' + __name__)

ADD_HOLIDAY_ERROR = "Holiday cannot be added!"
DATE_ERROR = "Incorrect date formatting!"
DATE_TYPE_ERROR = "The date entered is not of type date. Cannot generate desired information."
REMOVE_HOLIDAY_ERROR = "Holiday cannot be removed!"

dow = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday",
}

dom = {
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

    def __init__(self, start=date.today().year, end=None):
        """
        Constructor for watchmen.common.cal.py
        @param start: starting year to generate holidays
        @param end: exclusive ending year to generate holidays
        @note
        There are 3 different constructors:
            1) InfobloxCalendar()
                - This creates a calendar of holidays for the current year
            2) InfobloxCalendar(2020)
                - This creates a calendar for just the given year
            3) InfobloxCalendar(2020, 2090)
                - This creates a calendar for the given range of years
        """
        if end is None:
            end = start+1
        # How do I make this retain its changes after being given new holidays and there are no instances of the object?
        # Read a json file of holidays that need to be added and which ones to remove? Add and remove for each instance?
        # this file would need to be updated once a year

        self.holiday_list = holidays.US(state='WA', years=list(range(start, end)))

    def add_holiday(self, year=None, month=None, day=None, name='Custom Infoblox Holiday'):
        """
        Add a custom holiday to the holiday list
        @param year: of new holiday
        @param month: of new holiday
        @param day: of new holiday
        @param name: of new holiday
        @return: An exception if date attributes are None
        """
        try:
            new_date = '{}-{}-{}'.format(year, month, day)
            self.holiday_list.append({new_date: name})
        except Exception as e:
            message = "{}\nTrying to add holiday: Year-{} Month-{} Day-{}".format(ADD_HOLIDAY_ERROR, year, month, day)
            LOGGER.error(message)

    def _find_weekday(self, date_to_check):
        """
        Finds which day of the week the given date is
        @param date_to_check:
        @return: int value corresponding with the correct day of the week
        """
        if not isinstance(date_to_check, date):
            LOGGER.error(DATE_TYPE_ERROR)
            return None
        return dow.get(date_to_check.weekday())

    def _get_month(self, date_to_check):
        """
        Get the numeric value of the month for a given date
        @param date_to_check:
        @return: the numeric month
        """
        if not isinstance(date_to_check, date):
            LOGGER.error(DATE_TYPE_ERROR)
            return None

        return dom.get(date_to_check.month)

    def _is_weekend(self, day):
        """
        Determines if given day is a weekend day based on its weekday number.
        5 and 6 represent Saturday and Sunday. 0-4 are Mon-Fri.
        @param day: to be checked
        @return: whether or not the given day is a weekend day or not
        """
        week_num = day.weekday()
        if week_num < 5:
            return False
        return True

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
            if year is None or month is None or day is None:
                date_to_check = date.today()
            else:
                date_to_check = date(year, month, day)
        except Exception as e:
            message = "{}\nTrying to check : Year-{} Month-{} Day-{}".format(DATE_ERROR, year, month, day)
            LOGGER.error(message)
            return None

        if self._is_weekend(date_to_check) or (date_to_check in self.holiday_list):
            return False
        return True

    # I don't know how to make this more beautiful
    # Right now, great for debugging compile time errors
    def print_holidays(self):
        for date, name in sorted(self.holiday_list.items()):
            day_of_week = self._find_weekday(date)
            written_month = self._get_month(date)
            print('{}, {} {} {}: {}'.format(day_of_week, written_month, date.day, date.year, name))

    def remove_holiday(self, year=None, month=None, day=None):
        """
        Remove the given date from holiday list
        @param year: of date to be removed
        @param month: of date to be removed
        @param day: of date to be removed
        """
        try:
            new_date = '{}-{}-{}'.format(year, month, day)
            removed_date = self.holiday_list.pop(new_date)
            LOGGER.info('{} has been removed'.format(removed_date))
        except Exception as e:
            message = "{}\nTrying to remove holiday: Year-{} Month-{} Day-{}".format(REMOVE_HOLIDAY_ERROR, year, month, day)
            LOGGER.error(message)

    def main(self):
        print("TEST")

    # raise alert for new infoblox holidays


if __name__ == "__main__":
    cal = InfobloxCalendar(-2)
    cal.print_holidays()

