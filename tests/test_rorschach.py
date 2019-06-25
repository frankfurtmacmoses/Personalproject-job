"""
Created on May 23, 2017
@author: daltondb
"""
import importlib

import unittest
import datetime
import pytz
import os
import watchmen.process.rorschach as rorschach

from mock import patch
from mock import MagicMock
from watchmen.process.rorschach import \
    _EVERYTHING_ZERO_SIZE_MESSAGE, \
    _NOTHING_PARQUET_MESSAGE, \
    _NOTHING_RECENT_MESSAGE, \
    _FAILURE_HEADER, \
    _SUBJECT_EXCEPTION_MESSAGE, \
    _SUBJECT_MESSAGE, \
    _SUCCESS_HEADER


class TestRorschach(unittest.TestCase):

    def setUp(self):
        self.year = 2017
        self.month = 5
        self.day = 24
        self.hour = 8
        self.minute = 0
        self.example_now = datetime.datetime(
            year=self.year, month=self.month, day=self.day,
            hour=self.hour, minute=self.minute, tzinfo=pytz.utc)
        self.example_offset = 5
        self.example_dt_offset = datetime.timedelta(self.example_offset)
        self.example_check_time = self.example_now - self.example_dt_offset

        self.example_parquet_result = "Failure Occurred"
        self.example_status = "A giant header was created"
        self.example_exception_message = "Something really bad happened!"
        self.example_traceback = "Fake traceback"

        self.prefix_env = "parquet/magic_path/year=2017"
        self.bucket_env = "magic_bitaa"
        self.example_suffix = self.example_check_time.strftime(
            rorschach.RorschachWatcher.suffix_format)
        self.example_full_path = os.sep.join([self.prefix_env, self.example_suffix]) + os.sep

        self.example_message = "This is a Test, Ignore!"
        self.example_arn = 'arn:aws:sns:us-east-1:405093580753:Hancock'
        self.example_subject = "TEST: Example Subject Message"

        self.msg_format = "\n\t%s\n\t%s" % (self.example_full_path, self.example_check_time)
        self.not_recent_not_parquet_all_zero = \
            rorschach._NOTHING_RECENT_MESSAGE + \
            rorschach._NOTHING_PARQUET_MESSAGE + \
            rorschach._EVERYTHING_ZERO_SIZE_MESSAGE + \
            self.msg_format
        self.not_parquet_all_zero = \
            rorschach._NOTHING_PARQUET_MESSAGE + \
            rorschach._EVERYTHING_ZERO_SIZE_MESSAGE + \
            self.msg_format
        self.all_zero = rorschach._EVERYTHING_ZERO_SIZE_MESSAGE + \
            self.msg_format
        self.example_test_cases = {'FFF': [{'LastModified': self.example_now - datetime.timedelta(5)},
                                           {'LastModified': self.example_now + datetime.timedelta(5),
                                            'Size': 100,
                                            'Key': 'some/path/to/something.parquet'},
                                           {'LastModified': self.example_now - datetime.timedelta(1)}],
                                   'FFT': [{'LastModified': self.example_now + datetime.timedelta(5),
                                            'Size': 100,
                                            'Key': 'some/path/to/something'}],
                                   'FTF': [{'LastModified': self.example_now + datetime.timedelta(5),
                                            'Size': 0,
                                            'Key': 'some/path/to/something.parquet'}],
                                   'FTT': [{'LastModified': self.example_now + datetime.timedelta(5),
                                            'Size': 0,
                                            'Key': 'some/path/to/something'}],
                                   'TFF': [{'LastModified': self.example_now - datetime.timedelta(5),
                                            'Size': 100,
                                            'Key': 'some/path/to/something.parquet'}],
                                   'TFT': [{'LastModified': self.example_now - datetime.timedelta(5),
                                            'Size': 100,
                                            'Key': 'some/path/to/something'}],
                                   'TTF': [{'LastModified': self.example_now - datetime.timedelta(5),
                                            'Size': 0,
                                            'Key': 'some/path/to/something.parquet'}],
                                   'TTT': [{'LastModified': self.example_now - datetime.timedelta(5),
                                            'Size': 0,
                                            'Key': 'some/path/to/something'}]}

    def tearDown(self):
        pass

    @patch.object(os, 'getenv')
    @patch('datetime.timedelta')
    @patch('datetime.datetime')
    def createWatcher(self, mock_datetime, mock_timedelta, mock_getenv):
        mock_datetime.now.return_value = self.example_now
        mock_timedelta.return_value = self.example_dt_offset
        mock_getenv.side_effect = [self.prefix_env, self.bucket_env]
        importlib.reload(rorschach)
        return rorschach.RorschachWatcher()

    @staticmethod
    def resetWatcher(watcher):
        watcher.nothing_recent = True
        watcher.everything_zero_size = True
        watcher.nothing_parquet = True
        return watcher

    def test_constructor(self):

        # Test with Good prefix, bucket, check full path
        watcher = self.createWatcher()
        expected = self.example_full_path
        return_result = watcher.full_path
        self.assertEqual(expected, return_result)

        # Test with bad prefix
        rorschach.RorschachWatcher.prefix = None
        rorschach.RorschachWatcher.bucket = self.bucket_env
        self.assertRaises(AssertionError, rorschach.RorschachWatcher)

        # Test with bad bucket
        rorschach.RorschachWatcher.prefix = self.prefix_env
        rorschach.RorschachWatcher.bucket = None
        self.assertRaises(AssertionError, rorschach.RorschachWatcher)

    @patch('watchmen.utils.s3.generate_pages')
    def test_process_all_files(self, mock_generate_pages):

        expected = {
            'FFF': [False, False, False],
            'FFT': [False, False, True],
            'FTF': [False, True, False],
            'FTT': [False, True, True],
            'TFF': [True, False, False],
            'TFT': [True, False, True],
            'TTF': [True, True, False],
            'TTT': [True, True, True],
        }

        watcher = self.createWatcher()

        for key in expected:
            b = expected[key]
            watcher = self.resetWatcher(watcher)
            mock_generate_pages.reset_mock()
            mock_generate_pages.return_value = self.example_test_cases[key]
            watcher.process_all_files()
            msg = "test '{}' expects nothing_recent: {}, everything_zero_size: {}, nothing_parquet: {}".format(key,
                                                                                                               b[0],
                                                                                                               b[1],
                                                                                                               b[2])
            self.assertEqual(b[0], watcher.nothing_recent, msg)
            self.assertEqual(b[1], watcher.everything_zero_size, msg)
            self.assertEqual(b[2], watcher.nothing_parquet, msg)

    @patch('watchmen.process.rorschach.RorschachWatcher.process_all_files')
    @patch('watchmen.utils.s3.check_empty_folder')
    def test_summarize_parquet_stream(self, mock_check_empty_folder, mock_process_all_files):
        # Test with Empty Response!
        mock_check_empty_folder.return_value = (True, None)
        watcher = self.createWatcher()
        watcher.process_all_files = mock_process_all_files
        return_result = watcher.summarize_parquet_stream()
        expected_result = {
            "success": False,
            "subject": _SUBJECT_MESSAGE,
            "message": "The S3 bucket for today is empty or missing!  %s" % self.example_full_path
        }
        self.assertEqual(expected_result, return_result)

        # Test with all three True
        mock_check_empty_folder.reset_mock()
        mock_check_empty_folder.return_value = (False, [])
        watcher.nothing_recent = True
        watcher.nothing_parquet = True
        watcher.everything_zero_size = True
        return_result = watcher.summarize_parquet_stream()
        # Create message
        msg = ''
        msg += _NOTHING_RECENT_MESSAGE
        msg += _NOTHING_PARQUET_MESSAGE
        msg += _EVERYTHING_ZERO_SIZE_MESSAGE
        expected_result = {
            "success": False,
            "subject": _SUBJECT_MESSAGE,
            "message": msg
        }
        self.assertEqual(expected_result, return_result)

        # Test with all three False
        mock_check_empty_folder.reset_mock()
        watcher.nothing_recent = False
        watcher.nothing_parquet = False
        watcher.everything_zero_size = False
        mock_check_empty_folder.return_value = (False, [])
        return_result = watcher.summarize_parquet_stream()
        expected_result = {
            "success": True,
            "message": _SUCCESS_HEADER
        }
        self.assertEqual(expected_result, return_result)

    @patch('watchmen.process.rorschach._traceback.format_exc')
    @patch('watchmen.process.rorschach.RorschachWatcher.summarize_parquet_stream')
    def test_get_parquet_result(self, mock_check, mock_trace):
        mock_trace.return_value = self.example_traceback
        mock_check.return_value = self.example_parquet_result
        watcher = self.createWatcher()
        watcher.summarize_parquet_stream = mock_check
        expected = self.example_parquet_result
        returned = watcher.get_parquet_result()
        self.assertEqual(expected, returned)

        mock_check.side_effect = Exception(self.example_exception_message)
        msg = "An error occurred while checking the parquet at {} due to the following:\n\n{}\n\n".format(
            self.example_check_time, self.example_traceback)
        expected = {
            "success": False,
            "subject": _SUBJECT_EXCEPTION_MESSAGE,
            "message": msg + "\n\t%s\n\t%s" % (self.example_full_path, self.example_check_time)
        }
        returned = watcher.get_parquet_result()
        self.assertEqual(expected, returned)

    @patch('watchmen.utils.sns_alerts.raise_alarm')
    def test_notify(self, mock_alarm):
        test_results = [
            {
                "result": {
                    "success": True,
                    "message": _SUCCESS_HEADER
                },
                "expected": _SUCCESS_HEADER},
            {
                "result": {
                    "success": False,
                    "subject": self.example_subject,
                    "message": self.example_message
                },
                "expected": _FAILURE_HEADER
            }
        ]

        watcher = self.createWatcher()

        for result in test_results:
            parquet_result = result.get("result")
            expected = result.get("expected")
            returned = watcher.notify(parquet_result)
            self.assertEqual(expected, returned)

    @patch('watchmen.process.rorschach.RorschachWatcher')
    def test_main(self, mock_rorschach_watcher):
        mock_rorschach_instance = MagicMock()

        mock_rorschach_instance.get_parquet_result.return_value = self.example_parquet_result
        mock_rorschach_instance.notify.return_value = self.example_status
        mock_rorschach_watcher.return_value = mock_rorschach_instance

        expected = mock_rorschach_instance.notify()
        returned = rorschach.main(None, None)
        self.assertEqual(expected, returned)
