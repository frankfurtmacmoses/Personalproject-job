"""
tests/test_common_sum_result.py

@author: Kayla Ramos
@email: kramos@infoblox.com
@date: 2019-10-06
"""
import unittest

from watchmen.common.sum_result import \
    MESSAGE_TYPE_ERROR_MESSAGE, \
    MESSAGE_VALUE_ERROR_MESSAGE, \
    SUBJECT_TYPE_ERROR_MESSAGE, \
    SUBJECT_VALUE_ERROR_MESSAGE, \
    SUCCESS_TYPE_ERROR_MESSAGE

from watchmen.common.sum_result import SummarizedResult


class SummarizedResultTester(unittest.TestCase):

    def setUp(self):
        self.example_message = "I am an informative message"
        self.example_subject = "I am a good subject message"
        self.example_SummarizedResult = \
            SummarizedResult(success=True, message=self.example_message, subject=self.example_subject)

    def test_init_(self):
        success_error_tests = ["string", 'c', 9, -0.7, {"Hot": "Dog"}, [1, 2], None, ("Tuple", 5)]

        typeerror_tests = [True, 9, -0.7, {"Hot": "Dog"}, [1, 2], None, ("Tuple", 5)]

        empty_tests = [
            {
                "success": True,
                "message": "",
                "subject": self.example_subject,
                "err_msg": MESSAGE_VALUE_ERROR_MESSAGE
            }, {
                "success": False,
                "message": self.example_message,
                "subject": "",
                "err_msg": SUBJECT_VALUE_ERROR_MESSAGE
            }, {
                "success": True,
                "message": "",
                "subject": "",
                "err_msg": MESSAGE_VALUE_ERROR_MESSAGE
            }
        ]

        successful_test = {
            "success": False,
            "message": self.example_message,
            "subject": self.example_subject
        }

        for test in success_error_tests:
            with self.assertRaises(TypeError) as error:
                SummarizedResult(success=test, subject=self.example_subject, message=self.example_message)
            self.assertEqual(SUCCESS_TYPE_ERROR_MESSAGE, str(error.exception))

        for test in typeerror_tests:
            with self.assertRaises(TypeError) as error:
                SummarizedResult(success=False, subject=test, message=self.example_message)
            self.assertEqual(SUBJECT_TYPE_ERROR_MESSAGE, str(error.exception))

            with self.assertRaises(TypeError) as error:
                SummarizedResult(success=True, subject=self.example_subject, message=test)
            self.assertEqual(MESSAGE_TYPE_ERROR_MESSAGE, str(error.exception))

        for test in empty_tests:
            success = test.get('success')
            msg = test.get('message')
            subj = test.get('subject')
            err_msg = test.get('err_msg')

            with self.assertRaises(ValueError) as error:
                SummarizedResult(success=success, subject=subj, message=msg)
            self.assertEqual(err_msg, str(error.exception))

        # Missing Success
        with self.assertRaises(Exception):
            SummarizedResult(subject=self.example_subject, message=self.example_message)
        # Missing Subject
        with self.assertRaises(Exception):
            SummarizedResult(success=True, message=self.example_message)
        # Missing Message
        with self.assertRaises(Exception):
            SummarizedResult(success=False, subject=self.example_subject)

        # Success
        expected = successful_test
        returned = SummarizedResult(
            success=successful_test.get('success'),
            message=successful_test.get('message'),
            subject=successful_test.get('subject')).result
        self.assertEqual(expected, returned)

    def test_add_kv(self):
        kv_pairs = [
            ("String", "String"),
            ("char", '$'),
            ("int", 9),
            ("double", -.09),
            ("boolean", False),
            ("None", None)
        ]

        for k, v in kv_pairs:
            self.example_SummarizedResult.add_kv(key=k, value=v)
            self.assertIn(k, self.example_SummarizedResult.result)

    def test_log_result(self):
        expected = None
        returned = self.example_SummarizedResult.log_result()
        self.assertEqual(expected, returned)
