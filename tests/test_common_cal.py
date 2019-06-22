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
            "year": "2025", "month": 12, "day": 18,
        }, {
            "year": 2025, "month": "12", "day": 18,
        }, {
            "year": 2025, "month": 12, "day": "18",
        }, {
            "year": 2025, "month": 4.45, "day": 18,
        }, {
            "year": 2025, "month": 12, "day": None,
        }, {
            "year": 2025, "month": None, "day": 18,
        }, {
            "year": 2025, "month": 12, "day": -25,
        }, {
            "year": 2025, "month": 14, "day": 18,
        }, {
            "year": 2025, "month": 12, "day": 32,
        }, {
            "year": None, "month": 12, "day": 18,
        }, {
            "year": None, "month": None, "day": None,
        }, {
            "year": "", "month": "", "day": "",
        }, {
            "year": 0, "month": 12, "day": 18,
        }, {

        }]

        year = 2025
        month = 12
        day = 18
        name = "Kayla\'s Birthday"

        cal = InfobloxCalendar()

        # This holiday should have the default name
        cal.add_holiday(year, month, day)
        self.assertIn("Custom Infoblox Holiday", cal.holiday_list.values())

        # This is a second insertion of the above holiday but with a different name
        cal.add_holiday(year, month, day, name)
        self.assertIn("{}, Custom Infoblox Holiday".format(name), cal.holiday_list.values())

        # This is the second insertion of the above holiday exactly
        # No error because a list does not contain duplicates
        cal.add_holiday(year, month, day, name)

        for holiday in bad_holidays:
            cal.add_holiday(holiday.get('year'), holiday.get('month'), holiday.get('day'))
            self.assertRaises(Exception)

    def test_is_workday(self):
        dates = [{
            'year': 2019, 'month': 12, 'day': 18, 'expected': True,
        }, {
            'year': 2020, 'month': 2, 'day': 7, 'expected': True,
        }, {
            'year': 2029, 'month': 9, 'day': 10, 'expected': True,
        }, {
            'year': 2019, 'month': 4, 'day': 6, 'expected': False,
        }, {
            'year': 2020, 'month': 12, 'day': 25, 'expected': False,
        }, {
            'year': 2029, 'month': 1, 'day': 1, 'expected': False,
        }, {
            'year': 2025, 'month': 16, 'day': 10, 'expected': None,
        }, {
            'year': 2025, 'month': -10, 'day': 10, 'expected': None,
        }, {
            'year': 2025, 'month': 10, 'day': "15", 'expected': None,
        }]

        for d in dates:
            year = d.get('year')
            month = d.get('month')
            day = d.get('day')
            expected = d.get('expected')
            returned = InfobloxCalendar(2019, 2030).is_workday(year, month, day)
            self.assertEqual(expected, returned)

    def test_is_workhour(self):
        good_hours = [{
            "hour": 6, "expected": True,
        }, {
            "hour": 12, "expected": True,
        }, {
            "hour": 17, "expected": True,
        }]

        bad_hours = [{
            "hour": 0, "expected": False,
        }, {
            "hour": 2, "expected": False,
        },  {
            "hour": 18, "expected": False,
        }, {
            "hour": 23, "expected": False,
        }, {
            "hour": 36, "expected": False,
        }, {
            "hour": -6, "expected": False,
        }, {
            "hour": 15.2, "expected": False,
        }, {
            "hour": "12", "expected": False,
        }]

        for hour in good_hours:
            input = hour.get('hour')
            expected = hour.get('expected')
            returned = InfobloxCalendar.is_workhour(hour.get('hour'))
            msg = '{} should be a work hour.'.format(input)
            self.assertEqual(expected, returned, msg)

        for hour in bad_hours:
            input = hour.get('hour')
            expected = hour.get('expected')
            returned = InfobloxCalendar.is_workhour(hour.get('hour'))
            msg = '{} should not be a work hour.'.format(input)
            self.assertEqual(expected, returned, msg)

    def test_print_holidays(self):
        cal = InfobloxCalendar(2020)
        expected = None
        returned = cal.print_holidays()
        self.assertEqual(expected, returned)

    def test_remove_holiday(self):
        bad_removals = [{
            "year": None, "month": 12, "day": 18,
        }, {
            "year": 2026, "month": None, "day": 18,
        }, {
            "year": 2026, "month": 12, "day": None,
        }, {
            "year": 2026, "month": -12, "day": 18,
        }, {
            "year": 2026, "month": 12, "day": 3.6,
        }, {
            "year": 2026, "month": 23, "day": 18,
        }, {
            "year": "2026", "month": 12, "day": 18,
        }, {
            "year": "", "month": "", "day": "",
        }, {

        }]
        # Remove christmas
        year = 2027
        month = 12
        day = 25

        single_remove = "Memorial Day"
        multiple_remove = ["Thanksgiving", "Labor Day", "Veterans Day"]
        misspelled_holiday = "Chirstmas"

        cal = InfobloxCalendar()
        # Remove one holiday by String name
        cal.remove_holiday(names=single_remove)
        for key, value in dict(cal.holiday_list).items():
            self.assertIsNot(value, single_remove)

        # Remove multiple holidays by String name fom a list
        cal.remove_holiday(names=multiple_remove)
        for key, value in dict(cal.holiday_list).items():
            self.assertNotIn(value, multiple_remove)

        # Remove holiday with bad name
        cal.remove_holiday(names=misspelled_holiday)
        self.assertRaises(Exception)

        # Remove a holiday by year, month, day
        cal.remove_holiday(year, month, day)
        self.assertNotIn(date(year, month, day), cal.holiday_list)

        # Remove holiday twice (removing christmas again)
        cal.remove_holiday(year, month, day)
        self.assertRaises(Exception)

        # Removals that should cause errors
        for bad in bad_removals:
            cal.remove_holiday(bad.get('year'), bad.get('month'), bad.get('day'))
            self.assertRaises(Exception)

    def test_init_(self):
        test_years = [{"start": 1880, "end": None},
                      {"start": 3000, "end": None},
                      {"start": "1996", "end": None},
                      {"start": 14.66, "end": None},
                      {"start": [2002], "end": None},
                      {"start": date.today().year, "end": 1752},
                      {"start": date.today().year, "end": 3000},
                      {"start": date.today().year, "end": "2012"},
                      {"start": date.today().year, "end": 20.02}]

        for test in test_years:
            start = test.get("start")
            end = test.get("end")
            cal = InfobloxCalendar(start, end)
            years = [date.today().year]
            self.assertEqual(years, cal.year_range)
