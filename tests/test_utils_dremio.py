import unittest
from mock import patch
from requests.models import Response
from watchmen.utils.dremio import *


class TestDremio(unittest.TestCase):
    def setUp(self):
        self.ok_response = Response()
        self.ok_response.status_code = 200
        self.ok_response._content = b'{}'
        pass

    @patch('watchman.utils.dremio.request.get')
    def test_fetch_reflection_metadata(self, mock_request):
        pass

    def test_pull_reflection_status(self):
        pass

    @patch('watchman.utils.dremio.request.get')
    def test_get_reflection_list(self, mock_request):
        pass

    def test_pull_reflection_basic_info(self):
        pass

    @patch('watchmen.utils.dremio.boto3.session.Session.client.get_secret_value')
    @patch('watchmen.utils.dremio.boto3.session.Session')
    def get_secret(self, mock_session, mock_get_secrete_value):
        pass

    @patch('watchmen.utils.dremio.request.post')
    def test_generate_auth_token(self,mock_request):
        pass


if __name__ == '__main__':
    unittest.main()
