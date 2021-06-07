"""
test_common_result_svc.py
"""
from mock import patch, MagicMock
import unittest

from watchmen.common.sns_notifier import SnsNotifier
from watchmen.common.result_svc import ResultSvc
from watchmen.utils.logger import get_logger

LOGGER = get_logger('watchmen.' + __name__)


class TestResultSvc(unittest.TestCase):
    def setUp(self):
        """
        setup for test
        """
        self.test_list = [{
            "target": "Threatwave"
        }, {
            "target": "Psl"
        }, {
            "target": "Cyber-Intel Endpoints"
        }, {
            "target": "Generic"
        }]
        self.expected = [{
            "target": "Threatwave"
        }, {
            "target": "Psl"
        }, {
            "target": "Cyber-Intel Endpoints"
        }]
        self.test_result_list = [{
            "result": 1
        }, {
            "result": 2
        }]
        self.test_notifier_dict = {
            "target1":
                "notifier1",
            "target2":
                "notifier2"
        }
        self.test_sns_topic = "arn:aws:sns:us-east-1:405093580753:WatchmenTest"
        self.test_exception_msg = "some exception"
        pass

    def test__init__(self):
        """
        test watchmen.common.result_svc :: ResultSvc :: __init__
        """
        result_svc_obj = ResultSvc(self.test_result_list)
        self.assertEqual(self.test_result_list, result_svc_obj.result_list)
        pass

    @patch('watchmen.common.result_svc.settings')
    def test_build_test_sns_topic(self, mock_settings):

        tests = [
            {
                "settings": 'arn:aws:sns:{region}:{account_id}:WatchmenTest',
                "expected": 'arn:aws:sns:us-east-1:405093580753:WatchmenTest'
            }, {
                "settings": Exception(),
                "expected": None
            }
        ]

        for test in tests:
            result_svc_obj = ResultSvc(self.test_result_list)
            mock_settings.return_value = test.get("settings")
            result = result_svc_obj._build_test_sns_topic()
            self.assertEqual(result, test.get('expected'))

    @patch('watchmen.common.result_svc.get_class')
    def test_load_notifiers(self, mock_class):
        """
        test watchmen.common.result_svc :: ResultSvc :: _load_notifiers
        """
        SNS = {
            "Cyber-Intel Endpoints": {
                "notifier": "SnsNotifier",
                "sns": "arn:aws:sns:us-east-1:405093580753:Watchmen_Test"
            }
        }

        result_svc_obj = ResultSvc(self.test_result_list)
        mock_class.return_value = SNS
        expected = SNS
        returned = result_svc_obj._load_notifiers()
        self.assertEqual(expected, returned)

    def test_get_notifier(self):
        """
        test watchmen.common.result_svc :: ResultSvc :: _get_notifier
        """
        result_svc_obj = ResultSvc(self.test_result_list)

        class TestResult:
            target = 'Newly Observed Data'

        test_result = TestResult()
        expected = SnsNotifier
        returned = result_svc_obj._get_notifier(test_result)
        self.assertEqual(expected, returned)

        # when target name not found
        class TestWrongResults:
            target = 'target which does not exist'

        test_result = TestWrongResults
        expected = None
        returned = result_svc_obj._get_notifier(test_result)
        self.assertEqual(expected, returned)

    def test_get_sns_topic(self):
        """
        test watchmen.common.result_svc :: ResultSvc :: _get_sns_topic
        """
        result_svc_obj = ResultSvc(self.test_result_list)

        class TestResult:
            target = 'Newly Observed Data'

        test_result = TestResult()
        expected = result_svc_obj._build_test_sns_topic()
        returned = result_svc_obj._get_sns_topic(test_result)
        self.assertEqual(expected, returned)

        # when target name not found
        class TestWrongResults:
            target = 'target which does not exist'

        test_result = TestWrongResults
        expected = None
        returned = result_svc_obj._get_sns_topic(test_result)
        self.assertEqual(expected, returned)

        class EnvironmentVarAlt:
            target = 'Cyber-Intel Endpoints'

        test_result = EnvironmentVarAlt
        expected = result_svc_obj._build_test_sns_topic()
        returned = result_svc_obj._get_sns_topic(test_result)
        self.assertEqual(expected, returned)

    def test_remove_generic(self):
        """
        test watchmen.common.result_svc :: ResultSvc :: remove_generic
        """
        class TestResult:
            def __init__(self, val):
                self.target = val['target']

        results = [TestResult(result) for result in self.test_list]
        result_svc_obj = ResultSvc(results)
        test_returned = result_svc_obj._remove_generic(results)
        returned = []
        for test in test_returned:
            result = test.__dict__
            returned.append(result)
        expected = self.expected
        self.assertEqual(expected, returned)

        # test exception
        result_svc_obj = ResultSvc(self.test_list)
        returned = result_svc_obj._remove_generic(self.test_list)
        expected = None
        self.assertEqual(expected, returned)

    @patch('watchmen.common.result_svc.ResultSvc._remove_generic')
    @patch('watchmen.common.storage_service.StorageService.save_results')
    def test_save_results(self, mock_save_results, mock_remove_generic):
        """
        test watchmen.common.result_svc :: ResultSvc :: save_results
        """
        result_svc_obj = ResultSvc(self.test_list)
        mock_remove_generic = self.test_list
        result_svc_obj.save_results(mock_remove_generic)
        mock_save_results.assert_called()

        # test exception
        returned = result_svc_obj.save_results(None)
        expected = None
        self.assertEqual(expected, returned)

    @patch('watchmen.common.result_svc.ResultSvc._get_notifier')
    @patch('watchmen.common.result_svc.ResultSvc._get_sns_topic')
    def test_send_alert(self, mock_get_sns, mock_get_notifier):
        """
        test watchmen.common.result_svc :: ResultSvc :: send_alert
        """
        result_svc_obj = ResultSvc(self.test_result_list)

        mock_notifier = MagicMock()
        mock_get_notifier.return_value = mock_notifier
        mock_get_sns.return_value = self.test_sns_topic
        returned = result_svc_obj.send_alert()
        mock_notifier.assert_called()
        self.assertTrue(returned)

        # test exception
        mock_get_notifier.side_effect = Exception
        returned = result_svc_obj.send_alert()
        self.assertFalse(returned)
