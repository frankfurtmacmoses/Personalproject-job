import pytz
import unittest
from datetime import datetime
from mock import patch

from watchmen.process.metropolis import Metropolis
from watchmen.process.metropolis import \
    DATA_FILE, \
    MESSAGES, \
    GENERIC_TARGET


class TestMetropolis(unittest.TestCase):

    def setUp(self):
        self.example_csv_content = b'\xef\xbb\xbfex_attribute\r\nex_value_1\r\nex_value_2\r\nex_value_3'
        self.example_date = 'fake date'
        self.example_details = 'detailed message'
        self.example_exception_msg = 'some exception'
        self.example_failure_subject = 'failure subject'
        self.example_generic_result = 'generic result'
        self.example_message = "Example message"
        self.example_process_name = 'reaper'
        self.example_result_list = ['result1', 'result2', self.example_generic_result]
        self.example_snapshot = 'some snapshot'
        self.example_watchman_name = 'Metropolis'
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
        self.example_row_dict_for_reaper_metrics = {
            "process": "reaper",
            "3LCL": "200",
            "3UCL": "500",
            "time": "time2",
            "date": "random date",
            "source": "second source",
            "metric_type": "FQDN",
            "metric_description": "daily",
            "metric_value": "5"
        }
        self.example_row_dict_for_unknown_source = {
            "process": "reap",
            "3LCL": "200",
            "3UCL": "500",
            "time": "time2",
            "date": "random date",
            "source": "second source",
            "metric_type": "FQDN",
            "metric_description": "daily",
            "metric_value": "5"
        }
        self.example_summary_parameters = {
            "success": False,
            "disable_notifier": False,
            "state": self.example_state,
            "subject": MESSAGES.get("failure_subject").format(self.example_process_name),
            "short_message": MESSAGES.get("failure_message"),
            "target": "Reaper Metrics"
        }
        self.example_result_dict = {
            "details": self.example_details,
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "short_message": "Example message",
            "watchman_name": self.example_watchman_name,
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
            "short_message": "NO MESSAGE",
            "result_id": 0,
            "snapshot": self.example_snapshot,
            "watchman_name": self.example_watchman_name,
            "state": "to be changed",
            "subject": "to be changed",
            "success": False,
            "target": GENERIC_TARGET,
        }
        self.example_result_dict_not_loaded = {
            "details": MESSAGES.get("not_loaded_details").format(self.example_date, DATA_FILE, self.example_traceback),
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "short_message": MESSAGES.get("not_loaded_message"),
            "result_id": 0,
            "snapshot": {},
            "watchman_name": self.example_watchman_name,
            "state": "EXCEPTION",
            "subject": MESSAGES.get("not_loaded_subject"),
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
        self.example_metric_data = [
            {"source": "AIS", "metric": {"IPV4_TIDE_SUCCESS": 312, "IPV4": 156}},
            {"source": "BLOX_cyberint", "metric": {"FQDN_TIDE_SUCCESS": 783, "FQDN": 261}},
            {"source": "AIS", "metric": {"FQDN_TIDE_SUCCESS": 312, "FQDN": 20}}
        ]
        self.example_updated_indicator = {"IPV4": 156, "FQDN": 281}
        self.traceback = "Traceback created during exception catch."

    @staticmethod
    def _create_metropolis():
        """
        Create a metropolis object
        @return: <Metropolis> metropolis object
        """
        return Metropolis(context=None, event=None)

    def test_calculate_reaper_indicator_metrics(self):
        """
        watchmen.process.metropolis :: Metropolis :: _calculate_reaper_indicator_metrics
        """
        tests = [{
            "metric_data": self.example_metric_data,
            "expected": {"FQDN": 281, "IPV4": 156},
        }]
        for test in tests:
            metropolis = self._create_metropolis()
            metropolis._calculate_reaper_indicator_metrics(test.get("metric_data"))
            self.assertEqual(test.get("expected"), metropolis.reaper_metrics)

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
        expected = None, MESSAGES.get("min_and_max_error_message")
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
            "message_type": MESSAGES.get("success_details")
        }, {
            "row": self.example_row_dict_out_range,
            "threshold_check": False,
            "tb": None,
            "message_type": MESSAGES.get("failure_details")
        }, {
            "row": self.example_row_dict_wrong_range,
            "threshold_check": None,
            "tb": self.example_traceback,
            "message_type": MESSAGES.get("exception_details")
        }]
        for test in tests:
            row = test.get("row")
            threshold_check = test.get("threshold_check")
            tb = test.get("tb")
            message_type = test.get("message_type")
            date, source_name, met_type, met_desc, met_val, process_name = \
                row.get("date"), row.get("source"), row.get("metric_type"), \
                row.get("metric_description"), row.get("metric_value"), row.get("process")

            if message_type == MESSAGES.get("exception_details"):
                expected = MESSAGES.get("details_format").format(message_type.format(process_name,
                                                                 source_name, date, tb), met_type, met_desc,
                                                                 met_val, self.example_threshold_msg)
            else:
                expected = MESSAGES.get("details_format").format(message_type.format(process_name,
                                                                 source_name, date, tb), met_type, met_desc,
                                                                 met_val, self.example_threshold_msg)

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
            "subject": MESSAGES.get("generic_success_subject"),
            "state": "SUCCESS",
            "success": True,
            "short_message": MESSAGES.get("generic") + MESSAGES.get("success_message")
        }, {
            "checks": [True, False, True],
            "subject": MESSAGES.get("generic_fail_subject"),
            "state": "FAILURE",
            "success": False,
            "short_message": MESSAGES.get("generic") + MESSAGES.get("failure_message")
        }, {
            "checks": [None, True, True],
            "subject": MESSAGES.get("generic_exception_subject"),
            "state": "EXCEPTION",
            "success": False,
            "short_message": MESSAGES.get("generic") + MESSAGES.get("exception_message")
        }, {
            "checks": [True, False, None],
            "subject": MESSAGES.get("generic_fail_and_exception_subject"),
            "state": "EXCEPTION",
            "success": False,
            "short_message": MESSAGES.get("generic") + MESSAGES.get("failure_exception_message")
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
            expected["short_message"] = test.get("short_message")

            returned_dict = self._create_metropolis()._create_generic_result(
                generic_checks=generic_checks,
                generic_details=generic_details,
                generic_snapshot=generic_snapshot
            ).to_dict()

            # since metropolis does not give observed time, we don't test the time here

            returned_dict["dt_created"] = "2018-12-18T00:00:00+00:00"

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
            short_message=self.example_message
        )
        returned_dict = returned.to_dict()

        # since metropolis does not give observed time, we don't test the time here

        returned_dict["dt_created"] = "2018-12-18T00:00:00+00:00"

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
            "returned": "Moving Mean: 7 || Minimum: 5 || Maximum: 10",
        }, {
            "attr": self.example_row_dict_in_range_2,
            "returned": "Moving Mean: 5 || Minimum: 5 || Maximum: 5",
        }, {
            "attr": self.example_row_dict_wrong_value,
            "returned": "Moving Mean: 15 || Minimum: s || Maximum: 3",
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

    @patch('watchmen.process.metropolis.requests.get')
    @patch('watchmen.process.metropolis.traceback.format_exc')
    @patch('watchmen.process.metropolis.requests.getattr')
    def test_get_live_target_data(self, mock_request, mock_traceback, mock_getattr):
        expected = (False, MESSAGES.get('no_indicator_message').format('FQDN', 'reaper'))
        returned = self._create_metropolis()._get_live_target_data(self.example_row_dict_for_reaper_metrics)
        self.assertEqual(expected, returned)

        # test exception
        traceback = self.traceback
        mock_getattr.side_effect = Exception()
        mock_traceback.return_value = traceback

        expected = None, traceback
        returned = self._create_metropolis()._get_live_target_data(self.example_row_dict_for_unknown_source)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.metropolis.requests.get')
    @patch('watchmen.process.metropolis.traceback.format_exc')
    def test_get_reaper_data_exception(self, mock_traceback, mock_request):
        metropolis = self._create_metropolis()
        traceback = self.traceback
        mock_request.side_effect = Exception()
        mock_traceback.return_value = traceback

        expected = None, traceback
        returned = metropolis._get_reaper_data(self.example_row_dict_for_reaper_metrics)
        self.assertEqual(expected, returned)

        # Test get reaper request not getting called twice.
        metropolis.reaper_metrics = {"FQDN": 281, "IPV4": 1000}
        returned = metropolis._get_reaper_data(self.example_row_dict_for_reaper_metrics)
        self.assertEqual(self.example_row_dict_for_reaper_metrics['moving_mean'], metropolis.reaper_metrics['FQDN'])

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
            returned_dict["details"] = MESSAGES.get("not_loaded_details").format(
                                        self.example_date, DATA_FILE, self.example_exception_msg)
            # since metropolis does not give observed time, we don't test the time here
            returned_dict["dt_created"] = "2018-12-18T00:00:00+00:00"
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
