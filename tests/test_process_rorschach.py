import datetime
import importlib
from mock import patch
import os
import pytz
import unittest

from watchmen.common.result import Result
import watchmen.models.rorschach as rorschach
from watchmen.models.rorschach import \
    _EVERYTHING_ZERO_SIZE_MESSAGE, \
    _NOTHING_PARQUET_MESSAGE, \
    _NOTHING_RECENT_MESSAGE, \
    _SUBJECT_EXCEPTION_MESSAGE, \
    _SUBJECT_MESSAGE, \
    _SUCCESS_SUBJECT, \
    _SUCCESS_MESSAGE


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

        self.example_status = "A giant header was created"
        self.example_exception_details = "Something really bad happened!"
        self.example_traceback = "Fake traceback"
        self.example_parquet_result = "Failure Occurred"

        self.prefix_env = "parquet/com.farsightsecurity.300021"
        self.bucket_env = "bitaa"
        self.example_suffix = self.example_check_time.strftime(
            rorschach.Rorschach.suffix_format)
        self.example_full_path = os.sep.join([self.prefix_env, self.example_suffix]) + os.sep

        self.example_details = "This is a Test, Ignore!"
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
        self.example_fail_details = "some failure details"
        self.example_fail_subject = "some failure subject"
        self.example_result_dict = {
                "details": self.example_fail_details,
                "disable_notifier": False,
                "dt_created": "2018-12-18T00:00:00+00:00",
                "dt_updated": "2018-12-18T00:00:00+00:00",
                "is_ack": False,
                "is_notified": False,
                "message": "NO MESSAGE",
                "result_id": 0,
                "snapshot": None,
                "source": "Rorschach",
                "state": "FAILURE",
                "subject": "some failure subject",
                "success": False,
                "target": "Farsight Data",
        }

        # example result dict with time but not str
        self.example_result_dict_time = self.example_result_dict.copy()
        self.example_result_dict_time["dt_created"] = self.example_check_time
        self.example_result_dict_time["dt_updated"] = self.example_check_time
        self.example_result = Result(**self.example_result_dict_time)

        # adjust time in the reuslt for result
        self.example_result.observed_time = "2018-12-18T00:00:00+00:00"
        self.example_test_cases = {
            'FFF': [{'LastModified': self.example_now - datetime.timedelta(5)},
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

    @patch('datetime.timedelta')
    @patch('datetime.datetime')
    def createWatcher(self, mock_datetime, mock_timedelta):
        mock_datetime.now.return_value = self.example_now
        mock_timedelta.return_value = self.example_dt_offset
        importlib.reload(rorschach)
        return rorschach.Rorschach(event=None, context=None)

    @staticmethod
    def resetWatcher(watcher):
        watcher.nothing_recent = True
        watcher.everything_zero_size = True
        watcher.nothing_parquet = True
        return watcher

    def test_init_(self):
        """
        test watchmen.models.rorschach :: Rorschach :: __init__
        """

        # Positive test, test with Good prefix, bucket, check full path
        watcher = self.createWatcher()
        expected = self.example_full_path
        return_result = watcher.full_path
        self.assertEqual(expected, return_result)

        # negative tests
        negative_tests = [{
            "prefix": None,
            "bucket": self.bucket_env,
        }, {
            "prefix": self.prefix_env,
            "bucket": None,
        }, {
            "prefix": None,
            "bucket": None,
        }]
        for test in negative_tests:
            rorschach.Rorschach.prefix = test.get("prefix")
            rorschach.Rorschach.bucket = test.get("bucket")
        self.assertRaises(AssertionError, rorschach.Rorschach)

    @patch('watchmen.utils.s3.generate_pages')
    def test_process_all_files(self, mock_generate_pages):
        """
        test watchmen.models.rorschach :: Rorschach :: _process_all_files
        """
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
            watcher._process_all_files()
            fmt = "test '{}' expects nothing_recent: {}, everything_zero_size: {}, nothing_parquet: {}"
            msg = fmt.format(key, b[0], b[1], b[2])
            self.assertEqual(b[0], watcher.nothing_recent, msg)
            self.assertEqual(b[1], watcher.everything_zero_size, msg)
            self.assertEqual(b[2], watcher.nothing_parquet, msg)

    @patch('watchmen.models.rorschach.Rorschach._process_all_files')
    @patch('watchmen.utils.s3.check_empty_folder')
    def test_summarize_parquet_stream(self, mock_check_empty_folder, mock_process_all_files):
        """
        test watchmen.models.rorschach :: Rorschach :: _summarize_parquet_stream
        """
        # Test with Empty Response!
        mock_check_empty_folder.return_value = (True, None)
        watcher = self.createWatcher()
        watcher._process_all_files = mock_process_all_files
        return_result = watcher._summarize_parquet_stream()
        expected_result = {
            "success": False,
            "subject": _SUBJECT_MESSAGE,
            "details": "The S3 bucket for today is empty or missing!  %s" % self.example_full_path
        }
        self.assertEqual(expected_result, return_result)

        # Test with all three True
        mock_check_empty_folder.reset_mock()
        mock_check_empty_folder.return_value = (False, [])
        watcher.nothing_recent = True
        watcher.nothing_parquet = True
        watcher.everything_zero_size = True
        return_result = watcher._summarize_parquet_stream()
        # Create details
        msg = ''
        msg += _NOTHING_RECENT_MESSAGE
        msg += _NOTHING_PARQUET_MESSAGE
        msg += _EVERYTHING_ZERO_SIZE_MESSAGE
        expected_result = {
            "success": False,
            "subject": _SUBJECT_MESSAGE,
            "details": msg
        }
        self.assertEqual(expected_result, return_result)

        # Test with all three False
        mock_check_empty_folder.reset_mock()
        watcher.nothing_recent = False
        watcher.nothing_parquet = False
        watcher.everything_zero_size = False
        mock_check_empty_folder.return_value = (False, [])
        return_result = watcher._summarize_parquet_stream()
        expected_result = {
            "success": True,
            'subject': _SUCCESS_SUBJECT,
            "details": _SUCCESS_MESSAGE
        }
        self.assertEqual(expected_result, return_result)

    @patch('watchmen.models.rorschach._traceback.format_exc')
    @patch('watchmen.models.rorschach.Rorschach._summarize_parquet_stream')
    def test_get_parquet_result(self, mock_check, mock_trace):
        """
        test watchmen.models.rorschach :: Rorschach :: _get_parquet_result
        """
        mock_trace.return_value = self.example_traceback
        mock_check.return_value = self.example_parquet_result
        watcher = self.createWatcher()
        watcher._summarize_parquet_stream = mock_check
        expected = self.example_parquet_result
        returned = watcher._get_parquet_result()
        self.assertEqual(expected, returned)

        mock_check.side_effect = Exception(self.example_exception_details)
        msg = "An error occurred while checking the parquet at {} due to the following:\n\n{}\n\n".format(
            self.example_check_time, self.example_traceback)
        expected = {
            "success": None,
            "subject": _SUBJECT_EXCEPTION_MESSAGE,
            "details": msg + "\n\t%s\n\t%s" % (self.example_full_path, self.example_check_time)
        }
        returned = watcher._get_parquet_result()
        self.assertEqual(expected, returned)

    def test_create_result(self):
        """
        test watchmen.models.rorschach :: Rorschach :: _create_result
        """
        watcher = self.createWatcher()
        summary = {"success": False, "details": self.example_fail_details, "subject": self.example_fail_subject}
        result_dict = watcher._create_result(summary).to_dict()
        expected = self.example_result_dict

        # since rorschach does not give observed time, we don't test the time here

        result_dict["dt_created"] = "2018-12-18T00:00:00+00:00"
        result_dict["dt_updated"] = "2018-12-18T00:00:00+00:00"

        self.assertDictEqual(expected, result_dict)

    @patch('watchmen.models.rorschach.Rorschach._get_parquet_result')
    def test_monitor(self, mock_get_parquet):
        """
        test watchmen.models.rorschach :: Rorschach :: monitor
        """
        watcher = self.createWatcher()
        mock_get_parquet.return_value = {
            "success": False,
            "details": self.example_fail_details,
            "subject": self.example_fail_subject,
        }
        watcher._get_parquet_result = mock_get_parquet
        expected = self.example_result_dict
        result = watcher.monitor()[0].to_dict()

        # since rorschach does not give observed time, we don't test the time here
        result["dt_created"] = "2018-12-18T00:00:00+00:00"
        result["dt_updated"] = "2018-12-18T00:00:00+00:00"

        self.assertDictEqual(expected, result)
