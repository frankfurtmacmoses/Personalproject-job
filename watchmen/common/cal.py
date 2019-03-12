from datetime import date
import holidays

from watchmen.utils.logger import get_logger

LOGGER = get_logger('watchmen.' + __name__)

DATE_ERROR = "Incorrect date formatting!"


class InfobloxCalendar(object):

    holiday_list = holidays.US()

    def add_holiday(self):
        pass

    def _is_weekend(self, day):
        """
        Determines if given day is a weekend day
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
            message = "{}\n Trying to check {}-{}-{}".format(DATE_ERROR, year, month, day)
            LOGGER.error(message)
            return None

        if self._is_weekend(date_to_check) or (date_to_check in self.holiday_list):
            return False
        return True

    def main(self):
        print("TEST")


    # raise alert for new infoblox holidays


if __name__ == "__main__":
    cal = InfobloxCalendar()
    print("Is today a workday: {}".format(cal.is_workday(None, None,None)))
    #'1/2/20014'