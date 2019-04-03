"""
test_common_api.py
"""
import unittest

from mock import MagicMock, patch

from watchmen.common.api import get_api_data
from watchmen.utils.logger import get_logger

LOGGER = get_logger('watchmen.' + __name__)


class CommonApiTester(unittest.TestCase):

    @classmethod
    def teardown_class(cls):
        pass

    def setUp(self):
        """setup for test"""
        self.api_url = 'https://test.com/api/v1'
        self.headers = {
            "Authorization": "Token token={}".format('authz_token'),
            "Content-Type": "application/json"
        }
        pass

    def tearDown(self):
        """tearing down at the end of the test"""
        pass

    @patch('watchmen.common.api.requests')
    def test_get_api_data(self, mock_requests):
        _html = '<html><body></body></html>'
        tests = [{
            'status': 200, 'content': '{"a": 1, "x": 3.14}', 'type': 'application/json',
            'expected': {"a": 1, "x": 3.14}
        }, {
            'status': 200, 'content': '', 'type': 'application/json',
            'expected': Exception(),
        }, {
            'status': 200, 'content': _html,
            'expected': {'data': _html},
        }, {
            'status': 500, 'content': '',
            'expected': None,
        }, {
            'status': 408, 'content': '',
            'expected': None,
        }, {
        }]
        result = None
        num = 0
        for test in tests:
            test_content = test.get('content') or ''
            test_expected = test.get('expected')
            test_status = test.get('status')

            mock_data = MagicMock()
            mock_headers = {'content-type': test.get('type', 'text/html')}
            mock_res = MagicMock(
                headers=mock_headers, status_code=test_status, content=mock_data)
            mock_res.read.return_value = mock_data
            mock_requests.get.return_value = mock_res if test_status else None
            mock_data.decode.return_value = test_content
            msg = ('test #%02d: status={}, content={}' % num).format(
                test_status, test_content)
            if isinstance(test_expected, Exception):
                with self.assertRaises(Exception) as ctx:
                    ctx_msg = 'unable to read data from request'
                    result, status = get_api_data(self.api_url, self.headers)
                    self.assertEqual(status, test_status)
                    self.assertTrue(ctx_msg in str(ctx.exception), msg)
                    self.assertEqual(result, None, msg)
                pass
            else:
                result, status = get_api_data(self.api_url, self.headers)
                log = '{} <==> status: {}, result: {}'.format(msg, status, result)
                # LOGGER.debug("Result is %s and expected is %s",result, test_expected)
                self.assertEqual(result, test_expected, log)
            #     self.assertEqual(status, test_status)
            num += 1
        pass
