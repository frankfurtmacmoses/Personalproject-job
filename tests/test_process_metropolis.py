import pytz
import unittest
from datetime import datetime
from mock import patch

from watchmen.process.metropolis import Metropolis
from watchmen.process.metropolis import \
    DATA_FILE, \
    DETAILS_FORMAT, \
    EXCEPTION_DETAILS, \
    EXCEPTION_MESSAGE, \
    FAILURE_EXCEPTION_MESSAGE, \
    FAILURE_DETAILS, \
    FAILURE_MESSAGE, \
    FAILURE_SUBJECT, \
    GENERIC, \
    GENERIC_EXCEPTION_SUBJECT, \
    GENERIC_FAIL_AND_EXCEPTION_SUBJECT, \
    GENERIC_FAIL_SUBJECT, \
    GENERIC_SUCCESS_SUBJECT, \
    GENERIC_TARGET, \
    MIN_AND_MAX_ERROR_MESSAGE, \
    NOT_LOADED_DETAILS, \
    NOT_LOADED_MESSAGE, \
    NOT_LOADED_SUBJECT, \
    SUCCESS_DETAILS, \
    SUCCESS_MESSAGE


class TestMetropolis(unittest.TestCase):

    def setUp(self):
        self.example_csv_content = b'\xef\xbb\xbfex_attribute\r\nex_value_1\r\nex_value_2\r\nex_value_3'
        self.example_date = 'fake date'
        self.example_details = 'detailed message'
        self.example_exception_msg = 'some exception'
        self.example_failure_subject = 'failure subject'
        self.example_generic_result = 'generic result'
        self.example_message = "Example message"
        self.example_process_name = 'domain_counts'
        self.example_result_list = ['result1', 'result2', self.example_generic_result]
        self.example_snapshot = 'some snapshot'
        self.example_source = 'Metropolis'
        self.example_state = 'FAILURE'
        self.example_traceback = 'some exception'
        self.example_target = 'some target'
        self.example_threshold_msg = 'test threshold msg'
        self.example_today = datetime(year=2018, month=12, day=18, tzinfo=pytz.utc)
        self.example_today_str = self.example_today.strftime('%Y-%m-%d')
        self.example_dict_list = [
                {"ex_attribute": "ex_value_1"},
                {"ex_attribute": "ex_value_2"},
                {"ex_attribute": "ex_value_3"}
            ]
        self.example_dict_list_with_dates = [
            {"date": "date1"},
            {"date": "date1"},
            {"date": "date2"},
            {"date": "date3"},
            {"date": "date1"}
        ]
        self.example_row_dict_in_range_1 = {
            "process": "process1",
            "3LCL": "5",
            "3UCL": "10",
            "moving_mean": "7",
            "time": "time1",
            "date": "random date",
            "source": "first source",
            "metric_type": "total_count",
            "metric_description": "daily",
            "metric_value": "7"
        }
        self.example_row_dict_in_range_2 = {
            "process": "process1",
            "3LCL": "5",
            "3UCL": "5",
            "moving_mean": "5",
            "time": "time2",
            "date": "random date",
            "source": "second source",
            "metric_type": "total_count",
            "metric_description": "daily",
            "metric_value": "5"
        }
        self.example_row_dict_out_range = {
            "process": "process2",
            "3LCL": "6",
            "3UCL": "8",
            "moving_mean": "9",
            "time": "time1",
            "date": "random date",
            "source": "random source",
            "metric_type": "total_count",
            "metric_description": "daily",
            "metric_value": "7"
        }
        self.example_row_dict_wrong_range = {
            "process": "process3",
            "3LCL": "9",
            "3UCL": "3",
            "moving_mean": "8",
            "date": "random date",
            "source": "random source",
            "metric_type": "total_count",
            "metric_description": "daily",
            "metric_value": "7"
        }
        self.example_row_dict_wrong_value = {
            "process": "process3",
            "3LCL": "s",
            "3UCL": "3",
            "moving_mean": "15",
            "date": "random date",
            "source": "random source",
            "metric_type": "total_count",
            "metric_description": "daily",
            "metric_value": "7"
        }
        self.example_row_dict_wrong_key = {
            "wrong_key": "35",
        }
        self.example_summary_parameters = {
            "success": False,
            "disable_notifier": False,
            "state": self.example_state,
            "subject": FAILURE_SUBJECT.format(self.example_process_name),
            "message": FAILURE_MESSAGE,
            "target": "Domain Counts Metrics"
        }
        self.example_result_dict = {
            "details": self.example_details,
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            "is_notified": False,
            "message": "Example message",
            "source": self.example_source,
            "result_id": 0,
            "snapshot": self.example_snapshot,
            "state": self.example_state,
            "subject": self.example_failure_subject,
            "success": False,
            "target": self.example_target,
        }
        self.example_result_dict_generic = {
            "details": self.example_details,
            "disable_notifier": "to be changed",
            "dt_created": "2018-12-18T00:00:00+00:00",
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            "is_notified": False,
            "message": "NO MESSAGE",
            "result_id": 0,
            "snapshot": self.example_snapshot,
            "source": self.example_source,
            "state": "to be changed",
            "subject": "to be changed",
            "success": False,
            "target": GENERIC_TARGET,
        }
        self.example_result_dict_not_loaded = {
            "details": NOT_LOADED_DETAILS.format(self.example_date, DATA_FILE, self.example_traceback),
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            "is_notified": False,
            "message": NOT_LOADED_MESSAGE,
            "result_id": 0,
            "snapshot": {},
            "source": self.example_source,
            "state": "EXCEPTION",
            "subject": NOT_LOADED_SUBJECT,
            "success": False,
            "target": GENERIC_TARGET,
        }
        self.example_sources_per_process = {
            "process1": [self.example_row_dict_in_range_1, self.example_row_dict_in_range_2],
            "process2": [self.example_row_dict_out_range]
        }
        self.example_dict_list_with_rows = [
            self.example_row_dict_in_range_1,
            self.example_row_dict_in_range_2,
            self.example_row_dict_out_range
        ]

    @staticmethod
    def _create_metropolis():
        """
        Create a metropolis object
        @return: <Metropolis> metropolis object
        """
        return Metropolis(context=None, event=None)

    def test_check_against_threshold(self):
        """
        test watchmen.process.metropolis :: Metropolis :: _check_against_threshold
        """
        tests = [{
            "input_dict": self.example_row_dict_in_range_1,
            "returned": True,
        }, {
            "input_dict": self.example_row_dict_in_range_2,
            "returned": True,
        }, {
            "input_dict": self.example_row_dict_out_range,
            "returned": False,
        }]
        for test in tests:
            input_dict = test.get("input_dict")
            print('input dict: ', input_dict)
            expected = test.get("returned")
            returned = self._create_metropolis()._check_against_threshold(input_dict)
            self.assertEqual((expected, None), returned)

        # wrong range
        expected = None, MIN_AND_MAX_ERROR_MESSAGE
        returned = self._create_metropolis()._check_against_threshold(self.example_row_dict_wrong_range)
        self.assertEqual(expected, returned)

        # exception tests
        tests_ex = [{
            "input_dict": self.example_row_dict_wrong_value,
            "tb": ValueError,
        }, {
            "input_dict": self.example_row_dict_wrong_key,
            "tb": TypeError,
        }]
        for test in tests_ex:
            input_dict = test.get("input_dict")
            expected_tb_msg = test.get("tb")().__class__.__name__
            returned, returned_tb = self._create_metropolis()._check_against_threshold(input_dict)
            self.assertIsNone(returned)
            self.assertTrue(expected_tb_msg in returned_tb)

    def test_create_details(self):
        """
        test watchmen.process.metropolis :: Metropolis :: _create_details
        """
        tests = [{
            "row": self.example_row_dict_in_range_1,
            "threshold_check": True,
            "tb": None,
            "message_type": SUCCESS_DETAILS
        }, {
            "row": self.example_row_dict_out_range,
            "threshold_check": False,
            "tb": None,
            "message_type": FAILURE_DETAILS
        }, {
            "row": self.example_row_dict_wrong_range,
            "threshold_check": None,
            "tb": self.example_traceback,
            "message_type": EXCEPTION_DETAILS
        }]
        for test in tests:
            row = test.get("row")
            threshold_check = test.get("threshold_check")
            tb = test.get("tb")
            message_type = test.get("message_type")
            date, source_name, met_type, met_desc, met_val = \
                row.get("date"), row.get("source"), row.get("metric_type"), \
                row.get("metric_description"), row.get("metric_value")

            expected = DETAILS_FORMAT.format(message_type.format(source_name, date, tb), met_type, met_desc, met_val,
                                             self.example_threshold_msg)
            returned = self._create_metropolis()._create_details(
                row=row,
                threshold_check=threshold_check,
                threshold_message=self.example_threshold_msg,
                tb=tb
            )
            self.assertEqual(expected, returned)

    def test_create_generic_result(self):
        """
        watchmen.process.metropolis :: Metropolis :: _create_generic_result
        """
        tests = [{
            "checks": [True, True, True],
            "subject": GENERIC_SUCCESS_SUBJECT,
            "state": "SUCCESS",
            "success": True,
            "message": GENERIC + SUCCESS_MESSAGE
        }, {
            "checks": [True, False, True],
            "subject": GENERIC_FAIL_SUBJECT,
            "state": "FAILURE",
            "success": False,
            "message": GENERIC + FAILURE_MESSAGE
        }, {
            "checks": [None, True, True],
            "subject": GENERIC_EXCEPTION_SUBJECT,
            "state": "EXCEPTION",
            "success": False,
            "message": GENERIC + EXCEPTION_MESSAGE
        }, {
            "checks": [True, False, None],
            "subject": GENERIC_FAIL_AND_EXCEPTION_SUBJECT,
            "state": "EXCEPTION",
            "success": False,
            "message": GENERIC + FAILURE_EXCEPTION_MESSAGE
        }]

        for test in tests:
            generic_checks = test.get("checks")
            generic_details = self.example_details
            generic_snapshot = self.example_snapshot
            expected = self.example_result_dict_generic

            # change the values to be expected values
            expected["subject"] = test.get("subject")
            expected["state"] = test.get("state")
            expected["success"] = test.get("success")
            expected["disable_notifier"] = test.get("success")
            expected["message"] = test.get("message")

            returned_dict = self._create_metropolis()._create_generic_result(
                generic_checks=generic_checks,
                generic_details=generic_details,
                generic_snapshot=generic_snapshot
            ).to_dict()

            # since metropolis does not give observed time, we don't test the time here

            returned_dict["dt_created"] = "2018-12-18T00:00:00+00:00"
            returned_dict["dt_updated"] = "2018-12-18T00:00:00+00:00"

            self.assertEqual(expected, returned_dict)

    @patch('watchmen.process.metropolis.Metropolis._get_date_today')
    def test_create_not_loaded_result(self, mock_get_date):
        """
        test watchmen.process.metropolis :: Metropolis :: _create_not_loaded_result
        """
        mock_get_date.return_value = self.example_date
        expected_dict = self.example_result_dict_not_loaded
        returned_dict = self._create_metropolis()._create_not_loaded_result(self.example_exception_msg).to_dict()

        # since metropolis does not give observed time, we don't test the time here

        returned_dict["dt_created"] = "2018-12-18T00:00:00+00:00"
        returned_dict["dt_updated"] = "2018-12-18T00:00:00+00:00"

        self.assertEqual(expected_dict, returned_dict)

    def test_create_result(self):
        """
        test watchmen.process.metropolis :: Metropolis :: _create_result
        """
        expected_dict = self.example_result_dict
        returned = self._create_metropolis()._create_result(
            success=False,
            disable_notifier=False,
            state=self.example_state,
            subject=self.example_failure_subject,
            details=self.example_details,
            snapshot=self.example_snapshot,
            target=self.example_target,
            message=self.example_message
        )
        returned_dict = returned.to_dict()

        # since metropolis does not give observed time, we don't test the time here

        returned_dict["dt_created"] = "2018-12-18T00:00:00+00:00"
        returned_dict["dt_updated"] = "2018-12-18T00:00:00+00:00"

        self.assertEqual(expected_dict, returned_dict)

    def test_create_summary_parameters(self):
        """
        test watchmen.process.metropolis :: Metropolis :: _create_summary_parameters
        """
        expected = self.example_summary_parameters
        returned = self._create_metropolis()._create_summary_parameters(False, self.example_process_name)
        self.assertEqual(expected, returned)

    def test_create_threshold_message(self):
        """
        test watchmen.process.metropolis :: Metropolis :: _create_threshold_message
        """
        tests = [{
            "attr": self.example_row_dict_in_range_1,
            "returned": "Minimum: 5 || Maximum: 10 || Moving Mean: 7",
        }, {
            "attr": self.example_row_dict_in_range_2,
            "returned": "Minimum: 5 || Maximum: 5 || Moving Mean: 5",
        }, {
            "attr": self.example_row_dict_wrong_value,
            "returned": "Minimum: s || Maximum: 3 || Moving Mean: 15",
        }]
        for test in tests:
            attr_dict = test.get("attr")
            expected = test.get("returned")
            returned = self._create_metropolis()._create_threshold_message(attr_dict)
            self.assertEqual(expected, returned)

    def test_fill_sources_per_process(self):
        empty_sources_per_process = {
            "process1": [],
            "process2": []
        }
        expected = self.example_sources_per_process
        returned = self._create_metropolis()._fill_sources_per_process(empty_sources_per_process,
                                                                       self.example_dict_list_with_rows)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.metropolis.Metropolis._get_date_today')
    def test_get_data_by_date(self, mock_get_date):
        """
        test watchmen.process.metropolis :: Metropolis :: _get_data_by_date
        """
        mock_get_date.return_value = "date1"
        expected = [
            {"date": "date1"},
            {"date": "date1"},
            {"date": "date1"}
        ]
        date = self._create_metropolis()._get_date_today()
        returned = self._create_metropolis()._get_data_by_date(self.example_dict_list_with_dates, date)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.metropolis.datetime')
    def test_get_date_today(self, mock_datetime):
        """
        test watchmen.process.metropolis :: Metropolis :: _get_date_today
        """
        mock_datetime.now.return_value = self.example_today
        expected = self.example_today_str
        returned = self._create_metropolis()._get_date_today()
        self.assertEqual(expected, returned)

    @patch('watchmen.process.metropolis.Metropolis._read_csv')
    @patch('watchmen.process.metropolis.Metropolis._get_data_by_date')
    @patch('watchmen.process.metropolis.Metropolis._fill_sources_per_process')
    @patch('watchmen.process.metropolis.Metropolis._create_result')
    @patch('watchmen.process.metropolis.Metropolis._create_generic_result')
    def test_monitor(self, mock_create_generic_result, mock_create_result, mock_rows_today, mock_get_data_by_date,
                     mock_read_csv):
        """
        test watchmen.process.metropolis :: Metropolis :: monitor
        """
        mock_read_csv.return_value = 'mock', 'mock'
        mock_get_data_by_date.return_value = self.example_dict_list_with_rows
        mock_create_result.side_effect = ['result1', 'result2']
        mock_create_generic_result.return_value = self.example_generic_result
        mock_rows_today.return_value = self.example_sources_per_process
        expected = self.example_result_list
        returned = self._create_metropolis().monitor()
        self.assertEqual(expected, returned)

    @patch('watchmen.process.metropolis.get_csv_data')
    def test_monitor_exception(self, mock_get_csv_data):
        """
        test watchmen.process.metropolis :: Metropolis :: monitor
        @return:
        """
        tests = [TypeError, ValueError, TimeoutError, IndexError, Exception]

        for test in tests:
            mock_get_csv_data.side_effect = test
            expected_dict = self.example_result_dict_not_loaded
            returned_dict = self._create_metropolis().monitor()[0].to_dict()
            returned_dict["details"] = NOT_LOADED_DETAILS.format(self.example_date, DATA_FILE,
                                                                 self.example_exception_msg)
            # since metropolis does not give observed time, we don't test the time here
            returned_dict["dt_created"] = "2018-12-18T00:00:00+00:00"
            returned_dict["dt_updated"] = "2018-12-18T00:00:00+00:00"
            self.assertEqual(expected_dict, returned_dict)

    @patch('watchmen.utils.s3.get_content')
    def test_read_csv(self, mock_get_content):
        """
        test watchmen.process.metropolis :: Metropolis :: _read_csv
        """
        mock_get_content.return_value = self.example_csv_content
        expected = self.example_dict_list
        returned = self._create_metropolis()._read_csv()
        self.assertEqual((expected, None), returned)

    @patch('watchmen.process.metropolis.get_csv_data')
    def test_read_csv_exception(self, mock_get_csv):
        """
        test watchmen.process.metropolis :: Metropolis :: _read_csv
        Exception test
        """
        mock_get_csv.side_effect = Exception(self.example_traceback)
        expected = self.example_traceback
        returned, returned_tb = self._create_metropolis()._read_csv()
        self.assertIsNone(returned)
        self.assertTrue(expected in returned_tb)
