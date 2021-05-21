import unittest
from datetime import datetime
from mock import patch
from requests.models import Response
from watchmen.utils.github import get_repository_commits, get_repository_release


class TestGithub(unittest.TestCase):

    def setUp(self):
        self.bad_response = Response()
        self.bad_response.status_code = 500
        self.bad_response._content = b'{"itgood?": "itnot"}'

        self.half_response = Response()
        self.half_response.status_code = 200

        self.ok_response = Response()
        self.ok_response.status_code = 200
        self.ok_response._content = b'{"itgood?": "itgood"}'

        self.traceback = 'traceback'

    @patch('watchmen.utils.github.traceback.format_exc')
    @patch('watchmen.utils.github.requests.get')
    def test_get_repository_commits(self, mock_request, mock_traceback):
        """
        test watchmen.util.github :: _get_repository_commits
        """

        tests = [
            {
                # everything runs correctly
                "owner": "test",
                "repo": "test",
                "since": datetime.now(),
                "token": '123',
                "path": '/',
                "request": self.ok_response,
                "tb": None,
                "expected": self.ok_response.json()
            },
            {
                # non 200 code response
                "owner": "test",
                "repo": "test",
                "since": datetime.now(),
                "token": '123',
                "path": '/',
                "request": self.bad_response,
                "tb": self.traceback,
                "expected": None
            },
            {
                # Error in code
                "owner": "test",
                "repo": "test",
                "since": datetime.now(),
                "token": '123',
                "path": '/',
                "request": self.half_response,
                "tb": self.traceback,
                "expected": None
            },
            {
                # Error in code
                "owner": "test",
                "repo": "test",
                "since": datetime.now(),
                "token": '123',
                "path": '/',
                "request": Exception(),
                "tb": self.traceback,
                "expected": None
            },
            {
                # Error in code
                "owner": "test",
                "repo": "test",
                "since": datetime.now(),
                "token": None,
                "path": '/',
                "request": Exception(),
                "tb": self.traceback,
                "expected": None
            }
        ]
        for test in tests:
            mock_request.return_value = test.get('request')
            mock_traceback.return_value = test.get('tb')
            expected = (test.get('expected'), test.get('tb'))
            returned = get_repository_commits(owner=test.get('owner'),
                                              repo=test.get('repo'),
                                              since=test.get('since'),
                                              token=test.get('token'),
                                              path=test.get('path'))

            self.assertEqual(expected, returned)

    @patch('watchmen.utils.github.traceback.format_exc')
    @patch('watchmen.utils.github.requests.get')
    def test_get_repository_release(self, mock_request, mock_traceback):
        """
        test watchmen.util.github :: _get_repository_release
        """
        tests = [
            {
                # everything runs correctly
                "owner": "test",
                "repo": "test",
                "token": '123',
                "request": self.ok_response,
                "tb": None,
                "expected": self.ok_response.json()
            },
            {
                # non 200 code response
                "owner": "test",
                "repo": "test",
                "token": '123',
                "request": self.bad_response,
                "tb": self.traceback,
                "expected": None
            },
            {
                # error in code
                "owner": "test",
                "repo": "test",
                "token": '123',
                "request": self.half_response,
                "tb": self.traceback,
                "expected": None
            },
            {
                # error in code
                "owner": "test",
                "repo": "test",
                "token": None,
                "request": self.ok_response,
                "tb": None,
                "expected": self.ok_response.json()
            }
        ]
        for test in tests:
            mock_request.return_value = test.get('request')
            mock_traceback.return_value = test.get('tb')
            expected = (test.get('expected'), test.get('tb'))
            returned = get_repository_release(owner=test.get('owner'),
                                              repo=test.get('repo'),
                                              token=test.get('token'))

            self.assertEqual(expected, returned)
