from datetime import date
import unittest

from watchmen.common.cal import InfobloxCalendar
from watchmen.utils.logger import get_logger

LOGGER = get_logger('watchmen.' + __name__)


class TestJupiter(unittest.TestCase):

    def setUp(self):
        self.example_today = '12/18/2019'

    def test_add_holiday(self):
        bad_holidays = [{
            "year": None,
            "month": 12,
            "day": 18,
        }, {
            "year": 2025,
            "month": None,
            "day": 18,
        }, {
            "year": 2025,
            "month": 12,
            "day": None,
        }, {
            "year": "",
            "month": "",
            "day": "",
        }, {
        }]

        year = 2025
        month = 12
        day = 18
        name = "Kayla\'s Birthday"

        cal = InfobloxCalendar()
        cal.add_holiday(year, month, day, name)
        self.assertIn(date(year, month, day), cal.holiday_list)

        cal = InfobloxCalendar()
        for holiday in bad_holidays:
            cal.add_holiday(holiday.get('year'), holiday.get('month'), holiday.get('day'))
            self.assertRaises(Exception)

    def test_is_workday(self):
        dates = [{
            'year': 2019,
            'month': 12,
            'day': 18,
            'expected': True,
        }, {
            'year': 2020,
            'month': 2,
            'day': 7,
            'expected': True,
        }, {
            'year': 2029,
            'month': 9,
            'day': 10,
            'expected': True,
        }, {
            'expected': True,
        }, {
            'year': 2019,
            'month': 4,
            'day': 6,
            'expected': False,
        }, {
            'year': 2020,
            'month': 12,
            'day': 25,
            'expected': False,
        }, {
            'year': 2029,
            'month': 1,
            'day': 1,
            'expected': False,
        }, {
            'year': 2025,
            'month': 16,
            'day': 10,
            'expected': None,
        }]

        for date in dates:
            year = date.get('year')
            month = date.get('month')
            day = date.get('day')
            expected = date.get('expected')
            returned = InfobloxCalendar(2019, 2030).is_workday(year, month, day)
            self.assertEqual(expected, returned)

    def test_is_workhour(self):
        hours = [{
            "hour": 0,
            "expected": False,
        }, {
            "hour": 2,
            "expected": False,
        }, {
            "hour": 6,
            "expected": True,
        }, {
            "hour": 12,
            "expected": True,
        }, {
            "hour": 17,
            "expected": True,
        }, {
            "hour": 18,
            "expected": False,
        }, {
            "hour": 23,
            "expected": False,
        }]

        for hour in hours:
            self.assertEqual(InfobloxCalendar.is_workhour(hour.get('hour')), hour.get('expected'))

    def test_remove_holiday(self):
        bad_removals = [{
            "year": None,
            "month": 12,
            "day": 18,
        }, {
            "year": 2026,
            "month": None,
            "day": 18,
        }, {
            "year": 2026,
            "month": 12,
            "day": None,
        }, {
            "year": "",
            "month": "",
            "day": "",
        }, {
        }]
        # Remove christmas
        year = 2027
        month = 12
        day = 25

        single_remove = "Memorial Day"
        multiple_remove = ["Thanksgiving", "Labor Day", "Veterans Day"]

        cal = InfobloxCalendar()
        cal.remove_holiday(names=single_remove)
        for key, value in dict(cal.holiday_list).items():
            self.assertIsNot(value, single_remove)

        cal.remove_holiday(names=multiple_remove)
        for key, value in dict(cal.holiday_list).items():
            self.assertNotIn(value, multiple_remove)
        cal = InfobloxCalendar()
        cal.remove_holiday(year, month, day)
        self.assertNotIn(date(year, month, day), cal.holiday_list)

        cal = InfobloxCalendar()
        for bad in bad_removals:
            cal.remove_holiday(bad.get('year'), bad.get('month'), bad.get('day'))
            self.assertRaises(Exception)
