# -*- coding: utf-8 -*-
"""
# test_utils_extension

@author: Jason Zhu
@email: jzhu@infoblox.com
@created: 2017-02-22

"""
import os
import unittest

from watchmen.utils.extension import DictEncoder
from watchmen.utils.extension import get_attr
from watchmen.utils.extension import get_json
from watchmen.utils.logger import get_logger

LOGGER = get_logger('watchmen.' + __name__)


class EncodeTest(object):
    """class EncodeTest to test DictEncoder and pickle_object"""
    def __init__(self):
        """constructor for EncodeTest"""
        self.name = 'pickle class name'
        self.dump = 'dump property'
        self.test = 'pickle test'


class ExtensionTests(unittest.TestCase):
    """ExtensionTests
    ExtensionTests includes all unit tests for extension module
    """
    def setUp(self):
        self.test_path = os.path.dirname(os.path.realpath(__file__))
        self.proj_path = os.path.dirname(self.test_path)
        self.repo_path = os.path.dirname(self.proj_path)
        pass

    def tearDown(self):
        pass

    def test_DictEncoder(self):
        """
        test watchmen.utils.extension.DictEncoder
        """
        import json
        test = EncodeTest()
        expected = """
        {"test": "pickle test", "name": "pickle class name", "dump": "dump property"}
        """.strip()
        result = json.dumps(test, cls=DictEncoder)
        self.assertEqual(result, expected)

    def test_get_attr(self):
        """
        test watchmen.utils.extension.get_attr
        """
        aaa = ['a', 'aa', 'aaa']
        obj = [{
            'list': [{'a': 1}, {'b': 2}, {'c': {'c1': 31, 'c2': 32}}],
            'test': {'x': 100, 'y': 200, 'z': 'zzz'},
            'okey': True,
        }]
        self.assertEqual(get_attr(obj, *[0, 'list', 0, 'a']), 1)
        self.assertEqual(get_attr(obj, *[0, 'list', 2, 'c', 'c2']), 32)
        self.assertEqual(get_attr(obj, *[0, 'list', 2, 'd']), None)
        self.assertEqual(get_attr(obj, *[0, 'test', 'x']), 100)
        self.assertEqual(get_attr(obj, *[1, 'list']), None)
        self.assertEqual(get_attr(obj, *['foo']), None)
        self.assertEqual(get_attr(obj, *[aaa]), None)
        self.assertEqual(get_attr(aaa, *[3]), None)

    def test_get_json(self):
        """
        test watchmen.utils.extension.get_json
        """
        tests = [
            {
                "obj": {'a': ['a1', 'a2'], 'b': {'b1': 'b', 'b2': 'bb'}},
                "out": '{\n"a": [\n"a1", \n"a2"\n], \n"b": {\n"b1": "b", \n"b2": "bb"\n}\n}'
            }
        ]
        for test in tests:
            result = get_json(test['obj'], indent=0)
            self.assertEqual(result, test['out'])
