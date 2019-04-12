"""
Created on May 23, 2017
@author: daltondb
"""
import unittest
import datetime
import pytz
import os
from mock import patch
from mock import MagicMock
import watchmen.process.rorschach as rorschach


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
        reload(rorschach)
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
    @patch('watchmen.process.rorschach.RorschachWatcher.raise_alarm')
    @patch('watchmen.utils.s3.check_empty_folder')
    def test_check_parquet_stream(self, mock_check_empty_folder, mock_raise_alarm, mock_process_all_files):
        # Test with Empty Response!
        # should raise the alarm
        mock_check_empty_folder.return_value = (True, None)
        watcher = self.createWatcher()
        watcher.raise_alarm = mock_raise_alarm
        watcher.process_all_files = mock_process_all_files
        return_result = watcher.check_parquet_stream()
        expected_result = 1
        self.assertEqual(expected_result, return_result)
        mock_raise_alarm.assert_called_once_with("The S3 bucket for today is empty or missing!  %s"
                                                 % self.example_full_path)

        # Test with all three True
        mock_check_empty_folder.reset_mock()
        mock_raise_alarm.reset_mock()
        mock_check_empty_folder.return_value = (False, [])
        watcher.nothing_recent = True
        watcher.nothing_parquet = True
        watcher.everything_zero_size = True
        return_result = watcher.check_parquet_stream()
        expected_result = 1
        self.assertEqual(expected_result, return_result)
        mock_raise_alarm.assert_called_once_with(self.not_recent_not_parquet_all_zero)

        # Test with all three False
        mock_check_empty_folder.reset_mock()
        mock_raise_alarm.reset_mock()
        watcher.nothing_recent = False
        watcher.nothing_parquet = False
        watcher.everything_zero_size = False
        mock_check_empty_folder.return_value = (False, [])
        return_result = watcher.check_parquet_stream()
        expected_result = 0
        self.assertEqual(expected_result, return_result)
        self.assertFalse(mock_raise_alarm.called)

    @patch('watchmen.process.rorschach.RorschachWatcher.get_sns_client')
    def test_raise_alarm(self, mock_get_sns_client):

        expected_response = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock_sns_client = MagicMock()
        mock_sns_client.publish.return_value = expected_response
        mock_get_sns_client.return_value = mock_sns_client
        rorschach._SUBJECT_MESSAGE = self.example_subject
        # Test with successful publish
        rorschach.RorschachWatcher.raise_alarm(self.example_message)
        mock_sns_client.publish.assert_called_once_with(TopicArn=self.example_arn,
                                                        Message=self.example_message,
                                                        Subject=self.example_subject)

        # Test with key error  - Need to figure out why this happens sometimes.
        mock_sns_client.reset_mock()
        expected_response = {"It's over 9000!": 9001}
        mock_sns_client.publish.return_value = expected_response
        rorschach.RorschachWatcher.raise_alarm(self.example_message)
        mock_sns_client.publish.assert_called_once_with(TopicArn=self.example_arn,
                                                        Message=self.example_message,
                                                        Subject=self.example_subject)

        # Test with unsuccessful publish
        mock_sns_client.reset_mock()
        expected_response = {'ResponseMetadata': {
                                'RetryAttempts': 0, 'HTTPStatusCode': 400,
                                'RequestId': '37e288bd-24bd-5cb0-98f3-d94dda3e7306',
                                'HTTPHeaders': {
                                  'x-amzn-requestid': '37e288bd-24bd-5cb0-98f3-d94dda3e7306',
                                  'date': 'Tue, 25 Jul 2017 08:07:30 GMT',
                                  'content-length': '294', 'content-type': 'text/xml'}},
                             u'MessageId': '5706ed1d-3e52-5061-a2b5-bcedc0d10fd7'}
        mock_sns_client.publish.return_value = expected_response
        self.assertRaises(AssertionError, rorschach.RorschachWatcher.raise_alarm,
                          self.example_message)
        mock_sns_client.publish.assert_called_once_with(TopicArn=self.example_arn,
                                                        Message=self.example_message,
                                                        Subject=self.example_subject)

    @patch('watchmen.process.rorschach._boto3_session')
    def test_get_sns_client(self, mock_boto3_session):
        expected_result = "I'm a client!"
        mock_session = MagicMock()
        mock_session.client.return_value = expected_result
        mock_boto3_session.Session.return_value = mock_session
        returned_result = rorschach.RorschachWatcher.get_sns_client()
        self.assertEqual(expected_result, returned_result)
        mock_session.client.assert_called_once_with('sns')

    @patch('watchmen.process.rorschach.RorschachWatcher')
    def test_main(self, mock_rorschach_watcher):

        # Test with Pass Result
        expected_result = 0
        mock_rorschach_instance = MagicMock()
        mock_rorschach_instance.check_parquet_stream.return_value = expected_result
        mock_rorschach_watcher.return_value = mock_rorschach_instance
        returned_result = rorschach.main(None, None)
        self.assertEqual(expected_result, returned_result)

        # Test with Fail Result
        expected_result = 1
        mock_rorschach_instance.check_parquet_stream.return_value = expected_result
        returned_result = rorschach.main(None, None)
        self.assertEqual(expected_result, returned_result)

        # Test with exception thrown
        expected_result = 1
        mock_rorschach_instance.check_parquet_stream.side_effect = Exception('Something went wrong')
        returned_result = rorschach.main(None, None)
        self.assertEqual(expected_result, returned_result)
