from datetime import date
import holidays


class InfobloxCalendar(object):

    def __init__(self):
        self.today = date.today()
        self.holidays = holidays.US()

    def isWeekend(self):
        week_num = self.today.weekday()
        if week_num < 5:
            return False
        else:
            return True

    def isWorkDay(self):
        # if not holiday or weekend, return true
        if (self.isWeekend() or (self.today in self.holidays)):
            return False;
        return True

    def main(self):
        print "TEST"


if __name__ == "__main__":
    cal = InfobloxCalendar()
    print "Is today a workday: {}".format(cal.isWorkDay())
