import unittest

from watchmen.utils.csv import csv_string_to_dict


class TestCsv(unittest.TestCase):

    def setUp(self) -> None:
        pass

    def test_csv_string_to_dict(self):
        """
        test watchmen.utils.csv.csv_string_to_dict
        """
        tests = [
            {
                "string": "key1,key2,key3\na,b,c\n1,2,3",
                "returned": [{
                    "key1": "a",
                    "key2": "b",
                    "key3": "c",
                }, {
                    "key1": "1",
                    "key2": "2",
                    "key3": "3",
                }]
            }, {
                "string": "key1,key2,key3\na,b,c,d\n1,2,3,4",
                "returned": [{
                    "key1": "a",
                    "key2": "b",
                    "key3": "c",
                }, {
                    "key1": "1",
                    "key2": "2",
                    "key3": "3",
                }]
            }, {
                "string": "I'm\ngood\ngreat\nnot bad",
                "returned": [{
                    "I'm": "good",
                }, {
                    "I'm": "great",
                }, {
                    "I'm": "not bad",
                }]
            }
        ]

        for test in tests:
            input_string = test.get("string")
            expected = test.get("returned")
            returned = csv_string_to_dict(input_string)
            self.assertEqual(expected, returned)
