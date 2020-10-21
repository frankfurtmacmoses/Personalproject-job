"""
Test utils for S3 module

@author: Jason Zhu
@email: jzhu@infoblox.com
@created: 2017-02-05

"""
from __future__ import absolute_import
import unittest

import watchmen.utils.s3 as s3
from watchmen.utils.s3 import CONFIG, validate_file_on_s3, get_file_contents_s3
from botocore.exceptions import ClientError, ParamValidationError
from mock import Mock, MagicMock, patch
from moto import mock_s3


class TestS3(unittest.TestCase):
    """
    TestS3 includes all unit tests for watchmen.utils.s3 module
    """

    def get_keys_from_prefixes(self, prefixes):
        """
        get keys from test data
        """
        keys = []
        for prefix in prefixes:
            keys.append(prefix['Prefix'])
        return keys

    def setUp(self):
        self.mock_doFunc = MagicMock()
        self.mock_iterator = MagicMock()
        self.mock_paginator = MagicMock()
        self.mock_paginator.paginate.return_value = self.mock_iterator
        self.mock_client = MagicMock()
        self.mock_client.get_paginator.return_value = self.mock_paginator

        self.bucket = "mocked_bucket"
        self.doBadFunc = "this is not a function"
        self.doFunc = lambda x, **kwargs: self.mock_doFunc()
        self.err_boto3 = "boto3 err"
        self.err_boto3_msg = "boto3 client error"
        self.err_boto3_res = {
            'Error': {'Code': '500', 'Message': self.err_boto3_msg}}
        self.err_bucket = "param 'bucket' must be a valid existing S3 bucket"
        self.err_doFunc = "param 'a_func' must be a function"

        self.mock_client_err = ClientError(self.err_boto3_res, self.err_boto3)
        self.mock_exception = Exception('err', 'msg')
        self.mock_check_false = False, None
        self.mock_check_true = True, None

        self.mock_s3 = MagicMock()
        self.mock_s3_bucket = MagicMock()
        self.mock_s3.Bucket.return_value = self.mock_s3_bucket
        self.mock_s3_object = MagicMock()
        self.mock_s3.Object.return_value = self.mock_s3_object
        self.mock_s3_put_return = {
            'Expiration': 'string',
            'ETag': 'string',
            'ServerSideEncryption': 'AES256',
            'VersionId': 'string',
            'SSECustomerAlgorithm': 'string',
            'SSECustomerKeyMD5': 'string',
            'SSEKMSKeyId': 'string',
            'RequestCharged': 'requester'
        }  # see http://boto3.readthedocs.io/en/latest/reference/services/s3.html#S3.Client.put_object

        self.mock_client.put_object.return_value = self.mock_s3_put_return

        self.mock_session = MagicMock()
        self.mock_session.client.return_value = self.mock_client
        self.mock_session.resource.return_value = self.mock_s3

        # testing data
        self.mock_params_test_dirs = {
            'Bucket': self.bucket, 'Delimiter': '', 'Prefix': 'test'}
        self.mock_params_test_xmls = {
            'Bucket': self.bucket, 'Delimiter': '.xml', 'Prefix': 'test'}
        self.mock_params_test_json = {
            'Bucket': self.bucket, 'Delimiter': '.json', 'Prefix': 'test'}
        self.mock_params_more_keys = {
            'Bucket': self.bucket, 'Delimiter': '', 'Prefix': 'more'}
        self.mock_prefixes = {
            'test_dirs': {
                'dirs': [
                    # 1 with ".test/"
                    {u'Prefix': u'test/a/b/.test/'},
                ],
                # 2 in 'test' (prefix) and 2 in "sub-path"
                'keys': [
                    {u'Prefix': u'test/20170116/', u'Key': u'empty/'},
                    {u'Prefix': u'test/20170116/test1'},
                    {u'Prefix': u'test/abc/'},
                    {u'Prefix': u'test/abc/more_test2'},
                    {u'Prefix': u'test/a/b/'},
                    {u'Prefix': u'test/a/b/c/d/_test3'},
                ],
            },
            'test_xmls': {
                'dirs': [
                    # 1 with ".xml/"
                    {u'Prefix': u'test/a/b/.xml/'},
                ],
                # 3 in 'test' (prefix) and 4 in "sub-path" ended with ".xml"
                'keys': [
                    {u'Prefix': u'test/20170116_test1.xml'},
                    {u'Prefix': u'test/20170116_test2.xml'},
                    {u'Prefix': u'test/20170116_test3.xml'},
                    {u'Prefix': u'test/abc/more_test1.xml'},
                    {u'Prefix': u'test/abc/more_test2.xml'},
                    {u'Prefix': u'test/a/b/c/d/_test1.xml'},
                    {u'Prefix': u'test/a/b/c/d/_test2.xml'},
                ],
            },
            'test_json': {
                'dirs': [
                    # 1 with ".json/"
                    {u'Prefix': u'test/dir.json/'},
                ],
                # 4 in 'test' (prefix) and 2 in "sub-path" ended with ".json"
                'keys': [
                    {u'Prefix': u'test/20170116_test1.json'},
                    {u'Prefix': u'test/20170116_test2.json'},
                    {u'Prefix': u'test/20170116_test3.json'},
                    {u'Prefix': u'test/20170116_test4.json'},
                    {u'Prefix': u'test/a/b/c/d/_test1.json'},
                    {u'Prefix': u'test/a/b/c/d/_test2.json'},
                ],
            },
            'more_keys': {
                'dirs': [],
                # 2 in 'more' (prefix) ended with ".json"
                'keys': [
                    {u'Key': u'more/20170116_test1.json'},
                    {u'Key': u'more/20170116_test2.json'},
                ],
            },
        }
        self.mock_prefix_more_keys = self.mock_prefixes['more_keys']['keys']
        self.mock_prefix_test_json = self.mock_prefixes['test_json']['keys']
        self.mock_prefix_test_xmls = self.mock_prefixes['test_xmls']['keys']
        self.mock_prefix_test_dirs = self.mock_prefixes['test_dirs']['keys']
        self.mock_filename = "foo.json"
        self.mock_old_path = "dir1/original/path"
        self.mock_new_path = "dir2/new_path"

        self.example_path = "some/path/here"
        self.example_content_length_zero = {'ContentLength': 0}
        self.example_content_length = {'ContentLength': 200}
        self.example_s3_content = "Example content"

    def tearDown(self):
        print("\ndone: " + self.id())

    @classmethod
    def tearDownClass(cls):
        print("\ndone.")

    @patch('watchmen.utils.s3.boto3_session')
    def test_check_bucket_boto3_error(self, mock_boto3):
        """
        check_bucket should throw on session.resource exception
        """
        self.mock_session.resource.side_effect = self.mock_client_err
        mock_boto3.Session.return_value = self.mock_session
        with self.assertRaises(ClientError) as context:
            s3.check_bucket("any")
        self.assertTrue(self.err_boto3_msg in str(context.exception))

    @patch('watchmen.utils.s3.boto3_session')
    def test_check_bucket_s3_param_validation_error(self, mock_boto3):
        args = {'report': 'example_report'}
        self.mock_session.resource.side_effect = ParamValidationError(**args)
        mock_boto3.Session.return_value = self.mock_session
        with self.assertRaises(ParamValidationError):
            s3.check_bucket("any")

    @patch('watchmen.utils.s3.boto3_session')
    def test_check_bucket_s3_error(self, mock_boto3):
        """
        check_bucket should return False on head_bucket exception
        """
        mock_s3 = self.mock_s3
        mock_boto3.Session.return_value = self.mock_session

        mock_s3.meta.client.head_bucket.side_effect = self.mock_client_err
        result, tb = s3.check_bucket("any")
        self.assertFalse(result, "should return False on ClientError")

        mock_s3.meta.client.head_bucket.side_effect = self.mock_exception
        result, tb = s3.check_bucket("any")
        self.assertFalse(result, "should return False on Exception")

    @patch('watchmen.utils.s3.boto3_session')
    def test_check_bucket_true(self, mock_boto3):
        """
        check_bucket should return True on no error
        """
        mock_boto3.Session.return_value = self.mock_session
        result, tb = s3.check_bucket("any")
        self.assertTrue(result, "should return True on no error")

    @patch('watchmen.utils.s3.boto3_session')
    def test_check_empty_folder(self, mock_boto3):
        """
        test watchmen.utils.s3.check_empty_folder
        """
        mock_boto3.Session.return_value = self.mock_session
        ctx = [
            [{'Key': 'a/b'}],
            [{'Key': 'dir'}],
            [{'Key': 'dir/'}],
        ]
        tests = [
            {'k': '_key', 'r': (False, None), 'c': {}},
            {'k': 'a/b/', 'r': (True, None), 'c': {}},
            {'k': 'dir/', 'r': (False, ctx[0]), 'c': {'Contents': ctx[0]}},
            {'k': 'dir/', 'r': (False, ctx[1]), 'c': {'Contents': ctx[1]}},
            {'k': 'dir/', 'r': (True, ctx[2]), 'c': {'Contents': ctx[2]}},
        ]
        for test in tests:
            key_name, bucket = test['k'], self.bucket
            self.mock_client.list_objects.return_value = test['c']
            expr1, expr2 = test['r']
            result, contents = s3.check_empty_folder(key_name, bucket)
            self.assertEqual(
                contents, expr2, "Failed on test: {}".format(str(test)))
            self.assertEqual(
                result, expr1, "Failed on test: {}".format(str(test)))

    @patch('watchmen.utils.s3.get_key')
    def test_check_key(self, mock_get_key):
        """
        test watchmen.utils.s3.check_key
        """
        s3.check_key('abc', 'xyz')
        mock_get_key.assert_called_with('abc', 'xyz')

    @patch('watchmen.utils.s3.boto3_session')
    def test_check_prefix(self, mock_boto3):
        """
        test watchmen.utils.s3.check_prefix
        """
        mock_boto3.Session.return_value = self.mock_session
        s3.check_prefix('prefix-abc', 'bucket-xyz')
        self.mock_client.list_objects.assert_called_with(
            Bucket='bucket-xyz', Prefix='prefix-abc')

    @patch('watchmen.utils.s3.boto3_session')
    def test_check_size(self, mock_boto3):
        """
        test watchmen.utils.s3.check_size
        """
        mock_boto3.Session.return_value = self.mock_session
        for size in [-1, 0, 1, 99, 65535]:
            self.mock_client.get_object.return_value = {'ContentLength': size}
            result = s3.check_size('prefix/123/key', 'bucket-xyz')
            self.mock_client.get_object.assert_called_with(
                Bucket='bucket-xyz', Key='prefix/123/key')
            self.assertEqual(result, size > 0)

    @patch('watchmen.utils.s3.boto3_session')
    def test_check_size_exception(self, mock_boto3):
        """
        test watchmen.utils.s3.check_size on exception
        """
        mock_boto3.Session.return_value = self.mock_session
        self.mock_client.get_object.side_effect = self.mock_client_err
        result = s3.check_size('prefix/123', 'bucket-xyz')
        self.mock_client.get_object.assert_called_with(
            Bucket='bucket-xyz', Key='prefix/123')
        self.assertFalse(result)

    def test_clean_json(self):
        """
        test watchmen.utils.s3.clean_json
        """
        tests = [
            {
                'data': '[ { "a": "1", "b": "2", }, { "aa": "11", },]',
                'result': '[ { "a": "1", "b": "2" }, { "aa": "11" } ]'
            },
            {
                'data': '[ { "a": "1", }, { "aa": [1,2,3,] } ]',
                'result': '[ { "a": "1" }, { "aa": [1,2,3 ] } ]'
            },
        ]
        for test in tests:
            result = s3.clean_json(test['data'])
            self.assertEqual(result, test['result'])

    @patch('watchmen.utils.s3.boto3_session')
    @patch('watchmen.utils.s3.get_key')
    def test_copy_contents_to_bucket(self, mock_get_key, mock_boto3):
        """
        test watchmen.utils.s3.copy_contents_to_bucket
        """
        mock_boto3.Session.return_value = self.mock_session
        contents, key_name, bucket = "contents", "some/s3/key", self.bucket

        mock_get_key.return_value = None
        result = s3.copy_contents_to_bucket(contents, key_name, bucket)
        self.assertEqual(self.mock_client.delete_object.call_count, 0)
        self.mock_client.put_object.assert_called_with(
            Body=contents, Bucket=bucket, Key=key_name)
        self.assertEqual(result, self.mock_s3_put_return)

        mock_get_key.return_value = {}
        result = s3.copy_contents_to_bucket(contents, key_name, bucket)
        self.assertEqual(self.mock_client.delete_object.call_count, 1)
        self.mock_client.put_object.assert_called_with(
            Body=contents, Bucket=bucket, Key=key_name)
        self.assertEqual(result, self.mock_s3_put_return)

        self.mock_client.put_object.side_effect = self.mock_exception
        result = s3.copy_contents_to_bucket(contents, key_name, bucket)
        self.assertIsNone(result)

    @patch('watchmen.utils.s3.boto3_session')
    @patch('os.path.isfile')
    def test_copy_to_bucket(self, mock_isfile, mock_boto3):
        """
        copy_to_bucket should return True on no error
        """
        mock_isfile.return_value = True
        mock_boto3.Session.return_value = self.mock_session
        result = s3.copy_to_bucket("any_file", "prefix")
        self.assertTrue(result, "should return True on no error")

    @patch('watchmen.utils.s3.boto3_session')
    @patch('os.path.isfile')
    def test_copy_to_bucket_exception(self, mock_isfile, mock_boto3):
        """
        copy_to_bucket should return False on exception
        """
        mock_isfile.return_value = True
        mock_boto3.Session.return_value = self.mock_session
        self.mock_s3.meta.client.upload_file.side_effect = self.mock_exception
        result = s3.copy_to_bucket("any_file", "prefix")
        self.assertFalse(result, "should return False on exception")

    @patch('watchmen.utils.s3.boto3_session')
    @patch('os.path.isfile')
    def test_copy_to_bucket_isfile_False(self, mock_isfile, mock_boto3):
        """
        copy_to_bucket should return False if file does not exist
        """
        mock_isfile.return_value = False
        mock_boto3.Session.return_value = self.mock_session
        result = s3.copy_to_bucket("any_file", "prefix")
        self.assertFalse(result, "should return False if file does not exist")

    @patch('watchmen.utils.s3.boto3_session')
    def test_create_key(self, mock_boto3):
        """
        test watchmen.utils.s3.create_key
        """
        mock_boto3.Session.return_value = self.mock_session
        contents, key_name, bucket = "contents", "some/s3/key", self.bucket
        result = s3.create_key(contents, key_name, bucket)
        self.mock_session.client.assert_called_with('s3', config=CONFIG)
        self.mock_client.put_object.assert_called_with(
            Body=contents, Bucket=bucket, Key=key_name)
        self.assertEqual(result, self.mock_s3_put_return)

        self.mock_client.put_object.side_effect = self.mock_exception
        result = s3.create_key(contents, key_name, bucket)
        self.assertIsNone(result)

    @patch('watchmen.utils.s3.boto3_session')
    def test_delete_empty_folder(self, mock_boto3):
        """
        test watchmen.utils.s3.delete_empty_folder
        """
        mock_boto3.Session.return_value = self.mock_session
        tests = [
            {'k': '_key', 'r': False, 'c': {}},
            {'k': 'dir/', 'r': False, 'c': {}},
            {'k': 'dir/', 'r': False, 'c': {'Contents': [{'Key': 'a/b'}]}},
            {'k': 'dir/', 'r': True, 'c': {'Contents': [{'Key': 'dir/'}]}},
        ]
        for test in tests:
            key_name, bucket = test['k'], self.bucket
            self.mock_client.list_objects.return_value = test['c']
            result = s3.delete_empty_folder(key_name, bucket)
            self.assertEqual(
                result, test['r'], "Failed on test: {}".format(str(test)))
            if result:
                self.mock_client.delete_object.assert_called_with(
                    Bucket=self.bucket, Key=test['k'])

    @patch('watchmen.utils.s3.boto3_session')
    def test_delete_key(self, mock_boto3):
        """
        test watchmen.utils.s3.delete_key
        """
        mock_boto3.Session.return_value = self.mock_session
        key_name, bucket = "some/s3/key", self.bucket
        s3.delete_key(key_name, bucket)
        self.mock_client.delete_object.assert_called_with(
            Bucket=bucket, Key=key_name)

        self.mock_client.delete_object.side_effect = self.mock_client_err
        result = s3.delete_key(key_name, bucket)
        self.assertEqual(result, False)

    @patch('watchmen.utils.s3.boto3_session')
    def test_get_client(self, mock_boto3):
        """
        test watchmen.utils.s3.get_client
        """
        mock_boto3.Session.return_value = self.mock_session
        result = s3.get_client()
        self.mock_session.client.assert_called_with('s3', config=CONFIG)
        self.assertEqual(result, self.mock_client)

    @patch('watchmen.utils.s3.get_content')
    def test_get_csv_data(self, mock_get_content):
        """
        test watchmen.utils.s3.get_csv_data
        """
        tests = [{
            "content": b'\xef\xbb\xbfprocess,max,min,count'
                       b'\r\nprocess1,0,10,12\r\nprocess2,0,29,15\r\nsome_process,1000,1060,5',
            "returned": 'process,max,min,count\nprocess1,0,10,12\nprocess2,0,29,15\nsome_process,1000,1060,5'
        }, {
            "content": b'\xef\xbb\xbfex_attribute\r\nex_value_1\r\nex_value_2\r\nex_value_3',
            "returned": 'ex_attribute\nex_value_1\nex_value_2\nex_value_3'
        }]
        for test in tests:
            mock_get_content.return_value = test["content"]
            expected = test["returned"]
            returned = s3.get_csv_data(key_name=self.mock_filename, bucket=self.bucket)
            self.assertEqual(expected, returned)

    @patch('watchmen.utils.s3.boto3_session')
    def test_get_resource(self, mock_boto3):
        """
        test watchmen.utils.s3.get_resource
        """
        mock_boto3.Session.return_value = self.mock_session
        result = s3.get_resource()
        self.mock_session.resource.assert_called_with('s3', config=CONFIG)
        self.assertEqual(result, self.mock_s3)

    @patch('watchmen.utils.s3.boto3_session')
    def test_get_content(self, mock_boto3):
        """
        test watchmen.utils.s3.get_content to get content from s3 file
        """
        key_name, bucket = "some/s3/keyname", "s3_bucket"
        contents_tests = [u'{"key": "value"}', "contents", ""]
        mock_boto3.Session.return_value = self.mock_session

        for content in contents_tests:
            mock_response = dict(Body=MagicMock(), ContentLength=len(content))
            self.mock_client.get_object.return_value = mock_response
            mock_response['Body'].read.return_value = content
            result = s3.get_content(key_name, bucket)
            self.mock_client.get_object.assert_called_with(
                Bucket=bucket, Key=key_name)
            self.assertEqual(result, content)

    @patch('watchmen.utils.s3.boto3_session')
    def test_get_content_exception(self, mock_boto3):
        """
        test watchmen.utils.s3.get_content on exception
        """
        key_name, bucket = "some/s3/keyname", "s3_bucket"
        mock_boto3.Session.return_value = self.mock_session
        self.mock_client.get_object.side_effect = self.mock_client_err
        result = s3.get_content(key_name, bucket)
        self.assertEqual(result, None)

    @mock_s3
    @patch('watchmen.utils.s3.boto3.resource')
    def test_get_file_contents_s3(self, mock_resource):
        # Exception Occurs
        mock_resource.return_value.Object.return_value.get.side_effect = ClientError({}, {})
        expected = None
        returned = get_file_contents_s3(self.bucket, self.example_path)
        self.assertEqual(expected, returned)

    @patch('watchmen.utils.s3.get_content')
    def test_get_json_data(self, mock_get_content):
        """
        test watchmen.utils.s3.get_json_data
        """
        key_name, bucket = "part-", "b"
        contents = '''[
        {"prop1": "value1"},
        {"prop2": "value2"},
        {"prop3": "value3"}
        ]'''
        mock_get_content.return_value = contents
        result = s3.get_json_data(key_name, bucket)
        self.assertEqual(result[0]['prop1'], 'value1')
        self.assertEqual(result[1]['prop2'], 'value2')
        self.assertEqual(result[2]['prop3'], 'value3')

    @patch('watchmen.utils.s3.get_content')
    def test_get_json_data_exception(self, mock_get_content):
        """
        test watchmen.utils.s3.get_json_data on exception
        """
        key_name, bucket, contents = "k", "b", "contents"
        mock_get_content.return_value = contents
        result = s3.get_json_data(key_name, bucket)
        self.assertEqual(result, None)

    @patch('watchmen.utils.s3.boto3_session')
    @patch('watchmen.utils.s3.check_bucket')
    def test_get_json_files(self, mock_check, mock_boto3):
        """
        test watchmen.utils.s3.get_json_file for 'test/*.json' keys
        """
        self.mock_iterator.search.return_value = self.mock_prefix_test_json
        mock_check.return_value = self.mock_check_true
        mock_boto3.Session.return_value = self.mock_session

        keys = self.get_keys_from_prefixes(self.mock_prefix_test_json)
        result = s3.get_json_files("test", self.bucket)
        self.mock_client.get_paginator.assert_called_with('list_objects')
        self.mock_paginator.paginate.assert_called_with(
            **self.mock_params_test_json)
        self.mock_iterator.search.assert_called_with('CommonPrefixes')
        self.assertEqual(len(result), len(self.mock_prefix_test_json))
        self.assertEqual(result, keys)

    @patch('watchmen.utils.s3.boto3_session')
    def test_get_key(self, mock_boto3):
        """
        test watchmen.utils.s3.get_key
        """
        key_name = 'some/key'
        mock_boto3.Session.return_value = self.mock_session
        mock_object = Mock(key=key_name)  # mock an object property
        self.mock_s3_bucket.objects.filter.return_value = [mock_object]
        key = s3.get_key(key_name, 'bucket')
        self.mock_s3.Bucket.assert_called_with('bucket')
        self.mock_s3_bucket.objects.filter.assert_called_with(Prefix=key_name)
        self.assertEqual(key, mock_object)

    @patch('watchmen.utils.s3.boto3_session')
    def test_get_key_none(self, mock_boto3):
        """
        test watchmen.utils.s3.get_key
        """
        key_name = 'some/key'
        mock_boto3.Session.return_value = self.mock_session
        expected_result = None
        returned_result = s3.get_key(key_name, 'bucket')
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.utils.s3.boto3_session')
    @patch('watchmen.utils.s3.check_bucket')
    def test_get_keys(self, mock_check, mock_boto3):
        """
        test watchmen.utils.s3.get_keys for 'test/*.json' keys
        """
        self.mock_iterator.search.return_value = self.mock_prefix_test_json
        mock_check.return_value = self.mock_check_true
        mock_boto3.Session.return_value = self.mock_session

        keys = self.get_keys_from_prefixes(self.mock_prefix_test_json)
        result = s3.get_keys("test", ".json", bucket=self.bucket)
        self.mock_client.get_paginator.assert_called_with('list_objects')
        self.mock_paginator.paginate.assert_called_with(
            **self.mock_params_test_json)
        self.mock_iterator.search.assert_called_with('CommonPrefixes')
        self.assertEqual(len(result), len(self.mock_prefix_test_json))
        self.assertEqual(result, keys)

    @patch('watchmen.utils.s3.get_content')
    def test_get_parquet_data(self, mock_get_content):
        """
        test watchmen.utils.s3.get_json_data
        """
        key_name, bucket = "part-", "b"
        contents = '''
        {"prop1": "value1"}
        {"prop2": "value2"}
        {"prop3": "value3"}
        '''
        mock_get_content.return_value = contents
        result = s3.get_parquet_data(key_name, bucket)
        self.assertEqual(result[0], {"prop1": "value1"})
        self.assertEqual(result[1], {"prop2": "value2"})
        self.assertEqual(result[2], {"prop3": "value3"})

    @patch('watchmen.utils.s3.convert_parquet_to_json')
    @patch('watchmen.utils.s3.get_content')
    def test_get_parquet_data_exception(self, mock_get_content, mock_convert_parquet_to_json):
        key_name, bucket = "part-", "b"
        contents = '''
        {"prop1": "value1"}
        {"prop2": "value2"}
        {"prop3": "value3"}
        '''
        mock_get_content.return_value = contents
        mock_convert_parquet_to_json.side_effect = Exception("Something went wrong :(")
        expected_result = None
        returned_result = s3.get_parquet_data(key_name, bucket)
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.utils.s3.boto3_session')
    def test_mv(self, mock_boto3):
        """
        test watchmen.utils.s3.mv to move files in s3 bucket
        """
        mock_boto3.Session.return_value = self.mock_session
        oldkey = self.mock_old_path + "/" + self.mock_filename
        newkey = self.mock_new_path + "/" + self.mock_filename
        source = self.bucket + "/" + oldkey
        result = s3.mv(
            self.mock_old_path,
            self.mock_new_path,
            self.mock_filename,
            self.bucket)
        self.assertEqual(result, True)
        self.mock_client.copy_object.assert_called_once()
        self.mock_client.copy_object.assert_called_with(
            Bucket=self.bucket, CopySource=source, Key=newkey)
        self.mock_client.delete_object.assert_called_once()
        self.mock_client.delete_object.assert_called_with(
            Bucket=self.bucket, Key=oldkey)

    @patch('watchmen.utils.s3.boto3_session')
    def test_mv_exception(self, mock_boto3):
        """
        test watchmen.utils.s3.mv on exception
        """
        self.mock_client.copy_object.side_effect = self.mock_exception
        mock_boto3.Session.return_value = self.mock_session
        result = s3.mv("old", "new", "file", self.bucket)
        self.assertEqual(result, False)

    @patch('watchmen.utils.s3.boto3_session')
    def test_mv_key(self, mock_boto3):
        """
        test watchmen.utils.s3.mv_key to move key in s3 bucket
        """
        mock_boto3.Session.return_value = self.mock_session
        oldkey = self.mock_old_path + "/" + self.mock_filename
        newkey = self.mock_new_path + "/" + self.mock_filename
        source = self.bucket + "/" + oldkey
        result = s3.mv_key(oldkey, newkey, self.bucket)
        self.assertEqual(result, True)
        self.assertEqual(self.mock_s3.Object.call_count, 2)
        self.mock_s3_object.copy_from.assert_called_once()
        self.mock_s3_object.copy_from.assert_called_with(CopySource=source)
        self.mock_s3_object.delete.assert_called_once()
        self.mock_s3_object.delete.assert_called_with()

    @patch('watchmen.utils.s3.boto3_session')
    def test_mv_key_exception(self, mock_boto3):
        """
        test watchmen.utils.s3.mv_key on exception
        """
        self.mock_s3.Object.side_effect = self.mock_exception
        mock_boto3.Session.return_value = self.mock_session
        result = s3.mv_key("old", "new", self.bucket)
        self.assertEqual(result, False)

    def test_process_func(self):
        """
        test watchmen.utils.s3.process_func
        """
        s3.process_func("key-name", **{'kwargs': {}})

    def test_process_check_do_bad_func(self):
        """
        process should raise error on invalid doFunc parameter
        """
        with self.assertRaises(ValueError) as context:
            s3.process(self.doBadFunc, '', '', bucket=self.bucket)
        self.assertEqual(self.err_doFunc, str(context.exception))

    @patch('watchmen.utils.s3.check_bucket')
    def test_process_check_bucket_false(self, mock_check):
        """
        process should raise error on check_bucket exception
        """
        mock_check.return_value = self.mock_check_false
        with self.assertRaises(ValueError) as context:
            s3.process(self.doFunc, '', '', bucket=self.bucket)
        self.assertEqual(self.err_bucket, str(context.exception))

    @patch('watchmen.utils.s3.boto3_session')
    @patch('watchmen.utils.s3.check_bucket')
    def test_process_boto3_error(self, mock_check, mock_boto3):
        """
        process should raise error on boto3.client exception
        """
        mock_check.return_value = self.mock_check_true
        mock_boto3.Session.side_effect = self.mock_client_err
        with self.assertRaises(ClientError) as context:
            s3.process(self.doFunc, '', '', bucket=self.bucket)
        self.assertTrue(self.err_boto3_msg in str(context.exception))

    @patch('watchmen.utils.s3.boto3_session')
    @patch('watchmen.utils.s3.check_bucket')
    def test_process_json_keys(self, mock_check, mock_boto3):
        """
        process should be able to process 'test/*.json' keys
        """
        self.mock_iterator.search.return_value = self.mock_prefix_test_json
        mock_check.return_value = self.mock_check_true
        mock_boto3.Session.return_value = self.mock_session

        s3.process_json(self.doFunc, "test", bucket=self.bucket)
        self.mock_client.get_paginator.assert_called_with('list_objects')
        self.mock_paginator.paginate.assert_called_with(
            **self.mock_params_test_json)
        self.mock_iterator.search.assert_called_with('CommonPrefixes')
        self.assertEqual(
            self.mock_doFunc.call_count, len(self.mock_prefix_test_json))

    @patch('watchmen.utils.s3.boto3_session')
    @patch('watchmen.utils.s3.check_bucket')
    def test_process(self, mock_check, mock_boto3):
        """
        process should be able to process with no suffix
        """
        self.mock_iterator.search.return_value = self.mock_prefix_more_keys
        mock_check.return_value = self.mock_check_true
        mock_boto3.Session.return_value = self.mock_session

        s3.process(self.doFunc, "more", "", bucket=self.bucket)
        self.mock_client.get_paginator.assert_called_with('list_objects')
        self.mock_paginator.paginate.assert_called_with(
            **self.mock_params_more_keys)
        self.mock_iterator.search.assert_called_with('Contents')
        self.assertEqual(
            self.mock_doFunc.call_count, len(self.mock_prefix_more_keys))

    @patch('watchmen.utils.s3.boto3_session')
    @patch('watchmen.utils.s3.check_bucket')
    def test_process_json(self, mock_check, mock_boto3):
        """
        process should be able to process 'test/*.json' keys
        """
        self.mock_iterator.search.return_value = self.mock_prefix_test_json
        mock_check.return_value = self.mock_check_true
        mock_boto3.Session.return_value = self.mock_session

        s3.process(self.doFunc, "test", ".json", bucket=self.bucket)
        self.mock_client.get_paginator.assert_called_with('list_objects')
        self.mock_paginator.paginate.assert_called_with(
            **self.mock_params_test_json)
        self.mock_iterator.search.assert_called_with('CommonPrefixes')
        self.assertEqual(
            self.mock_doFunc.call_count, len(self.mock_prefix_test_json))

    @patch('watchmen.utils.s3.boto3_session')
    @patch('watchmen.utils.s3.check_bucket')
    def test_process_xml(self, mock_check, mock_boto3):
        """
        process should be able to process 'test/*.xml' keys
        """
        self.mock_iterator.search.return_value = self.mock_prefix_test_xmls
        mock_check.return_value = self.mock_check_true
        mock_boto3.Session.return_value = self.mock_session

        s3.process(self.doFunc, "test", ".xml", bucket=self.bucket)
        self.mock_client.get_paginator.assert_called_with('list_objects')
        self.mock_paginator.paginate.assert_called_with(
            **self.mock_params_test_xmls)
        self.mock_iterator.search.assert_called_with('CommonPrefixes')
        self.assertEqual(
            self.mock_doFunc.call_count, len(self.mock_prefix_test_xmls))

    @patch('watchmen.utils.s3.boto3_session')
    @patch('watchmen.utils.s3.check_bucket')
    def test_process_keys(self, mock_check, mock_boto3):
        """
        process should be able to process with no suffix
        """
        self.mock_iterator.search.return_value = self.mock_prefix_test_dirs
        mock_check.return_value = self.mock_check_true
        mock_boto3.Session.return_value = self.mock_session

        counts = s3.process_keys(self.doFunc, "test", bucket=self.bucket)
        self.mock_client.get_paginator.assert_called_with('list_objects')
        self.mock_paginator.paginate.assert_called_with(
            **self.mock_params_test_dirs)
        self.mock_iterator.search.assert_called_with('Contents')
        # Minus 1 at the end since the directory gets removed
        self.assertEqual(counts, len(self.mock_prefix_test_dirs) - 1)

    @patch('watchmen.utils.s3.boto3_session')
    @patch('watchmen.utils.s3.check_bucket')
    def test_generate_pages(self, mock_check, mock_boto3):
        """
        process should be able to process with no suffix
        """
        self.mock_iterator.search.return_value = self.mock_prefix_more_keys
        self.mock_iterator.search.return_value.append({u'Key': u'more/20170116/'})
        mock_check.return_value = self.mock_check_true
        mock_boto3.Session.return_value = self.mock_session

        res = s3.generate_pages("test", bucket=self.bucket)

        # Only first two work.
        for dir in self.mock_prefix_more_keys[:2]:
            self.assertDictEqual(dir, next(res))
        # last one raises exception
        with self.assertRaises(StopIteration):
            next(res)
        self.mock_client.get_paginator.assert_called_with('list_objects')

        mock_params_called_with = \
            {'Bucket': 'mocked_bucket', 'Delimiter': '', 'PaginationConfig': {'MaxItems': None}, 'Prefix': 'test'}
        self.mock_paginator.paginate.assert_called_with(
            **mock_params_called_with)

        self.mock_iterator.search.assert_called_with('Contents')

    @mock_s3
    @patch('watchmen.utils.s3.boto3.resource')
    def test_validate_file_on_s3(self, mock_resource):
        # When file size is zero
        mock_resource.return_value.Object.return_value.get.return_value = self.example_content_length_zero
        expected = False
        returned = validate_file_on_s3(self.bucket, self.example_path)
        self.assertEqual(expected, returned)

        # When file size is non-zero
        mock_resource.return_value.Object.return_value.get.return_value = self.example_content_length
        expected = True
        returned = validate_file_on_s3(self.bucket, self.example_path)
        self.assertEqual(expected, returned)

        # When a client error occurs
        mock_resource.return_value.Object.return_value.get.side_effect = ClientError({}, {})
        expected = False
        returned = validate_file_on_s3(self.bucket, self.example_path)
        self.assertEqual(expected, returned)
