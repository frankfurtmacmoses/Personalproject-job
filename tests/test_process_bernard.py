import datetime
import unittest
from mock import patch
from moto import mock_emr

from watchmen.process.bernard import Bernard, EMR_TARGET, MESSAGES


class TestBernard(unittest.TestCase):

    def setUp(self):
        self.example_details = 'detailed message'
        self.example_json_file = 'emr_clusters_to_check.json'
        self.example_result_list = ['result1']
        self.success_details = MESSAGES.get("success_details")
        self.traceback = "Traceback created during exception catch."
        self.example_cluster_info = {
            "success": True,
            "details": ""
        }
        self.example_cluster_dict = {
            "step_clusters": [
                {
                    "cluster_name": "cyberintel-mining-algorithms-prod"
                },
                {
                    "cluster_name": "CyberIntel Sinkhole Detector"
                },
                {
                    "cluster_name": "ParkingDomain_Miner"
                },
                {
                    "cluster_name": "CyberIntel CDN Detector"
                },
                {
                    "cluster_name": "CyberIntel Cryptocurrency Detector"
                }
            ]
        }
        self.example_cluster_list = ["cyberintel-mining-algorithms-prod", "CyberIntel Sinkhole Detector",
                                     "ParkingDomain_Miner", "CyberIntel CDN Detector",
                                     "CyberIntel Cryptocurrency Detector"]
        self.example_emr_return = {'Clusters': [{'Id': 'j-3BEYCAG31GW3J', 'Name': 'CyberIntel CDN Detector', 'Status':
                                                {'State': 'TERMINATED', 'StateChangeReason': {},
                                                 'Timeline': {'CreationDateTime': datetime.datetime(2020, 7, 16, 10),
                                                              'EndDateTime': datetime.datetime(2020, 7, 16, 5)}}}]}
        self.example_failed_cluster = [{'Id': 'j-3BEYCAG31GW3J', 'Name': 'CyberIntel CDN Detector', 'Status':
                                       {'State': 'TERMINATED_WITH_ERRORS',
                                        'StateChangeReason': {'Code': 'VALIDATION_ERROR'},
                                        'Timeline': {'CreationDateTime': datetime.datetime(2020, 7, 16, 10, 23, 19),
                                                     'EndDateTime': datetime.datetime(2020, 7, 16, 5, 34, 40)}}}]
        self.example_hung_cluster = [{'Id': 'j-3BEYCAG31GW3J', 'Name': 'CyberIntel CDN Detector', 'Status':
                                     {'State': 'RUNNING', 'StateChangeReason': {},
                                      'Timeline': {'CreationDateTime': datetime.datetime(2020, 7, 16, 10, 23, 19)
                                                   }}}]
        self.example_list_clusters = {'Clusters': [{'Id': 'j-3BEYCAG31GW3J', 'Name': 'ParkingDomain_Miner'}]}
        self.example_list_clusters_return = [{'Id': 'j-3BEYCAG31GW3J', 'Name': 'ParkingDomain_Miner'}]
        self.example_parameters = {
                "details": self.success_details,
                "disable_notifier": True,
                "short_message": MESSAGES.get("success_short_message"),
                "snapshot": {},
                "state": "SUCCESS",
                "subject": MESSAGES.get("success_subject"),
                "success": True,
        }
        self.example_status_fail_input = {'Id': 'j-3BEYCAG31GW3J', 'Name': 'CyberIntel CDN Detector', 'Status':
                                          {'State': 'TERMINATED_WITH_ERRORS',
                                           'StateChangeReason': {'Code': 'VALIDATION_ERROR'},
                                           'Timeline': {'CreationDateTime': datetime.datetime(2020, 7, 1, 4, 30, 52),
                                                        'ReadyDateTime': datetime.datetime(2020, 7, 1, 4, 40, 26),
                                                        'EndDateTime': datetime.datetime(2020, 7, 4, 6, 37, 12)}}}
        self.example_status_input = {'Id': 'j-3BEYCAG31GW3J', 'Name': 'CyberIntel CDN Detector', 'Status':
                                     {'State': 'TERMINATED', 'StateChangeReason': {'Code': 'ALL_STEPS_COMPLETED'},
                                      'Timeline': {'CreationDateTime': datetime.datetime(2020, 7, 1, 4, 30, 52),
                                                   'ReadyDateTime': datetime.datetime(2020, 7, 1, 4, 40, 26),
                                                   'EndDateTime': datetime.datetime(2020, 7, 1, 5, 37, 12)}}}
        self.example_hung_cluster_within_limit = {'Id': 'j-3BEYCAG31GW3J', 'Name': 'CyberIntel CDN Detector', 'Status':
                                                  {'State': 'RUNNING', 'StateChangeReason': {'Code': 'STEPS_RUNNING'},
                                                   'Timeline': {'CreationDateTime': datetime.datetime(2020, 7, 1, 4, 3),
                                                                'ReadyDateTime': datetime.datetime(2020, 7, 1, 4, 40)}}}
        self.example_hung_cluster_fail = {'Id': 'j-3BEYCAG31GW3J', 'Name': 'CyberIntel CDN Detector', 'Status':
                                          {'State': 'RUNNING', 'StateChangeReason': {'Code': 'STEPS_RUNNING'},
                                           'Timeline': {'CreationDateTime': datetime.datetime(2020, 6, 30, 4, 30, 52),
                                                        'ReadyDateTime': datetime.datetime(2020, 7, 1, 4, 40, 26)}}}
        self.example_step_cluster = [{'Id': 'j-3BEYCAG31GW3J', 'Name': 'CyberIntel CDN Detector', 'Status':
                                     {'State': 'TERMINATED', 'StateChangeReason': {},
                                      'Timeline': {'CreationDateTime': datetime.datetime(2020, 7, 16, 10, 23, 19),
                                                   'EndDateTime': datetime.datetime(2020, 7, 16, 5, 34, 40)}}},
                                     {'Id': 'j-UN2KKGXOHAYM', 'Name': 'CyberIntel Sinkhole Detector', 'Status':
                                     {'State': 'TERMINATED', 'StateChangeReason': {'Code': 'STEPS_COMPLETED'},
                                      'Timeline': {'CreationDateTime': datetime.datetime(2020, 7, 16, 4, 30, 52),
                                                   'EndDateTime': datetime.datetime(2020, 7, 16, 5, 34, 40)}}}]
        self.example_successful_results = [{
            "details": MESSAGES.get("success_details"),
            "disable_notifier": True,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "short_message": MESSAGES.get("success_short_message"),
            "watchman_name": "Bernard",
            "result_id": 0,
            "snapshot": {},
            "state": "SUCCESS",
            "subject": MESSAGES.get("success_subject"),
            "success": True,
            "target": EMR_TARGET
        }]
        self.emr_check_tests = [{
            "input_status": self.example_status_input,
            "cluster_check_info": self.example_cluster_info,
            "expected": True,
        }, {
            "input_status": self.example_status_fail_input,
            "cluster_check_info": self.example_cluster_info,
            "expected": False,
        }]

    @staticmethod
    def _create_bernard():
        """
        Create a bernard object
        @return: <Bernard> bernard object
        """
        return Bernard(context=None, event=None)

    def test_check_successful_cluster_termination(self):
        """
        watchmen.process.bernard :: Bernard :: _check_failed_cluster
        """
        for test in self.emr_check_tests:
            bernard = self._create_bernard()
            returned = bernard._check_successful_cluster_termination(test.get('input_status'),
                                                                     test.get("cluster_check_info"))
            self.assertEqual((test.get('expected')), returned)

    @patch('watchmen.process.bernard.traceback.format_exc')
    @patch("watchmen.process.bernard.datetime")
    def test_check_cluster_runtime(self, mock_datetime, mock_traceback):
        """
        watchmen.process.bernard :: Bernard :: _check_hung_cluster
        """
        mock_datetime.now.return_value = datetime.datetime(year=2020, month=7, day=1, hour=6)
        self.emr_check_tests = [{
            "input_status": self.example_hung_cluster_within_limit,
            "cluster_check_info": self.example_cluster_info,
            "expected": True,
        }, {
            "input_status": self.example_hung_cluster_fail,
            "cluster_check_info": self.example_cluster_info,
            "expected": False,
        }]
        for test in self.emr_check_tests:
            bernard = self._create_bernard()
            bernard._check_cluster_runtime(test.get('input_status'),
                                           test.get('cluster_check_info'))
            self.assertEqual((test.get('expected')), test.get('cluster_check_info').get('success'))

        # exception tests
        traceback = self.traceback
        mock_traceback.return_value = traceback
        self._create_bernard()._check_cluster_runtime(self.example_list_clusters,
                                                      self.example_cluster_info)
        self.assertEqual(None, test.get('cluster_check_info').get('success'))

    @patch("watchmen.process.bernard.datetime")
    def test_check_step_clusters(self, mock_datetime):
        """
        watchmen.process.bernard :: Bernard :: _check_step_clusters
        """
        mock_datetime.now.return_value = datetime.datetime(year=2020, month=7, day=17, hour=6)
        tests = [{
            "cluster_list": self.example_step_cluster,
            "expected": True
        }, {
            "cluster_list": self.example_failed_cluster,
            "expected": False
        }, {
            "cluster_list": self.example_hung_cluster,
            "expected": False
        }]
        for test in tests:
            bernard = self._create_bernard()
            returned = bernard._check_step_clusters(self.example_cluster_list, test.get("cluster_list"))
            self.assertEqual(test.get('expected'), returned.get("success"))

    def test_create_result(self):
        """
        watchmen.process.bernard :: Bernard :: _create_result
        """
        bernard_obj = self._create_bernard()
        expected = self.example_successful_results
        returned = bernard_obj._create_result(self.example_parameters)

        returned_result = returned[0].to_dict()

        returned_result["dt_created"] = "2018-12-18T00:00:00+00:00"

        self.assertEqual(expected[0], returned_result)

    def test_create_result_parameters(self):
        """
        watchmen.process.bernard :: Bernard :: _create_result_parameters
        """
        bernard_obj = self._create_bernard()
        expected = self.example_parameters
        returned = bernard_obj._create_result_parameters(True, self.success_details)
        self.assertEqual(expected, returned)

    @mock_emr
    @patch('boto3.client')
    def test_get_emr_clusters(self, mock_client):
        """
        watchmen.process.bernard :: Bernard :: _get_emr_clusters
        """
        tests = [{
            "list_cluster_return": self.example_list_clusters,
            "step_expected": self.example_list_clusters_return
        }]
        for test in tests:
            mock_client.return_value.list_clusters.return_value = test.get("list_cluster_return")

            step_result = self._create_bernard()._get_emr_clusters()
            self.assertEqual(test.get('step_expected'), step_result)

    @patch('watchmen.process.bernard.json.loads')
    @patch('watchmen.process.bernard.json.load')
    @patch('watchmen.process.bernard.get_content')
    def test_load_clusters_to_check(self, mock_get_content, mock_load, mock_loads):
        """
        test watchmen.process.bernard :: Bernard :: _load_clusters_to_check
        """
        bernard_obj = self._create_bernard()

        mock_loads.return_value = self.example_cluster_dict
        expected, expected_msg = self.example_cluster_list, None
        returned, returned_msg = bernard_obj._load_clusters_to_check()
        self.assertEqual(expected, returned)
        self.assertEqual(expected_msg, returned_msg)

        # exception occurs
        ex_tests = [TimeoutError, TypeError, Exception, KeyError, ValueError]
        for exception in ex_tests:
            # Make the initial json.load() for the S3 file fail, as well as the nested json.loads() for the local file.
            mock_load.side_effect = exception
            mock_loads.side_effect = exception
            expected, expected_msg = None, exception().__class__.__name__
            returned, returned_msg = bernard_obj._load_clusters_to_check()
            self.assertEqual(expected, returned)
            self.assertTrue(expected_msg in returned_msg)

    @mock_emr
    @patch('boto3.client')
    @patch('watchmen.process.bernard.Bernard._load_clusters_to_check')
    @patch('watchmen.process.bernard.Bernard._create_result')
    def test_monitor(self, mock_create_result, mock_load_clusters, mock_client):
        mock_load_clusters.return_value = self.example_cluster_list, None
        mock_client.return_value.list_clusters.return_value = self.example_emr_return
        mock_create_result.side_effect = [['result1']]
        expected = self.example_result_list
        returned = self._create_bernard().monitor()
        self.assertEqual(expected, returned)

    @patch('watchmen.process.bernard.json.loads')
    @patch('watchmen.process.bernard.json.load')
    @patch('watchmen.process.bernard.Bernard._create_result')
    def test_monitor_exception(self, mock_create_result, mock_load, mock_loads):
        """
        test watchmen.process.bernard :: Bernard :: monitor
        @return:
        """
        bernard_obj = self._create_bernard()
        mock_create_result.side_effect = [['result1']]

        # Make the initial json.load() for the S3 file fail, as well as the nested json.loads() for the local file.
        mock_load.side_effect = TimeoutError
        mock_loads.side_effect = TimeoutError
        expected = ['result1']
        returned = bernard_obj.monitor()
        self.assertEqual(expected, returned)
