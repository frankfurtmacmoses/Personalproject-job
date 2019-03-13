from datetime import date
import unittest
from mock import patch

from watchmen.common.cal import InfobloxCalendar

from watchmen.utils.logger import get_logger

LOGGER = get_logger('watchmen.' + __name__)



class TestJupiter(unittest.TestCase):

    def setUp(self):
        self.example_today = '12/18/2019'

    def test_add_holiday(self):
        year = 2025
        month = 12
        day = 18
        name = "Kayla\'s Birthday"

        cal = InfobloxCalendar()
        cal.add_holiday(year, month, day, name)
        self.assertIn(date(year, month, day), cal.holiday_list)

        cal = InfobloxCalendar()
        cal.add_holiday(year, None, day, name)
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
            returned = InfobloxCalendar().is_workday(year, month, day)
            self.assertEqual(expected, returned)
