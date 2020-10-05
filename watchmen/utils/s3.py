"""
# s3 module includes functions for AWS S3 bucket and files

@author: Jason Zhu
@email: jzhu@infoblox.com
@created: 2017-02-01

@notes: The following environment variables are needed for AWS connection

AWS_DEFAULT_REGION=us-west-2
AWS_SECRET_ACCESS_KEY=
AWS_ACCESS_KEY_ID=

"""
import json
import traceback
import types
from logging import getLogger

import boto3
import boto3.session as boto3_session
import botocore
from botocore.client import Config
from botocore.exceptions import ClientError
from watchmen import const

LOGGER = getLogger(__name__)

FILE_SIZE_ZERO_ERROR_MESSAGE = "FILE SIZE IS ZERO!"
FILE_NOT_FOUND_ERROR_MESSAGE = "FILE DOESN'T EXIST!"

BUCKET_DEFAULT = 'cyber-intel'
MAX_ATTEMPTS = 2
PREFIX_PROCESSED = 'hancock/processed-json'
PREFIX_MINED = 'hancock/mined-json'
# This config is used with sessions. Otherwise, it will try to reconnect until the lambda times out
# with an exponential wait time in between each attempt. This sets a timeout time and no attempt to reconnect.
# If a session times out, it throws a ConnectionTimeout error and moves on.
CONFIG = Config(connect_timeout=5, retries={'max_attempts': MAX_ATTEMPTS})


def check_arg_bucket(bucket):
    """
    Check if the arg is a valid bucket; otherwise, raise ValueError
    """
    bucket_exists, tb = check_bucket(bucket)
    if not bucket_exists:
        raise ValueError("param 'bucket' must be a valid existing S3 bucket")


def check_arg_as_func(a_func):
    """
    Check if the arg is a function or method; otherwise, raise ValueError
    """
    is_func = isinstance(a_func, types.FunctionType) or isinstance(
        a_func, types.MethodType)
    if not is_func:
        LOGGER.error("param 'a_func' is " + type(a_func).__name__)
        raise ValueError("param 'a_func' must be a function")


def check_bucket(bucket_name):
    """
    Checks if a S3 bucket exists
    @param bucket_name: the bucket name (top-level directory in S3)
    @return: A boolean: True if bucket exists, False if bucket doesn't exist, None if an exception occurred.
             A traceback message: Traceback message if an exception is encountered, or None.
    """
    s3_resource = get_resource()

    try:
        s3_resource.meta.client.head_bucket(Bucket=bucket_name)
    except (botocore.exceptions.ClientError, botocore.exceptions.ParamValidationError) as botocore_exception:
        # If a client error is thrown and it is a 404 error, the bucket just doesn't exist.
        error_code = int(botocore_exception.response['Error']['Code'])
        if error_code == 404:
            return False, None
        else:
            LOGGER.error("ERROR Checking S3 bucket!")
            LOGGER.info(const.MESSAGE_SEPARATOR)
            LOGGER.exception('{}: {}'.format(type(botocore_exception).__name__, botocore_exception))
            tb = traceback.format_exc()
            return None, tb
    except Exception as ex:
        LOGGER.error("ERROR Checking S3 bucket!")
        LOGGER.info(const.MESSAGE_SEPARATOR)
        LOGGER.exception('{}: {}'.format(type(ex).__name__, ex))
        tb = traceback.format_exc()
        return None, tb

    return True, None


def check_empty_folder(key_name, bucket=BUCKET_DEFAULT):
    """
    check if an S3 folder (key suffix '/') is empty

    @return: a tuple of (bool, object) where the bool indicates if
             the key named folder is empty, and the object is the s3
             contents (None means an invalid or non-folder key)
    """
    if not str(key_name).endswith('/'):
        return (False, None)

    empty = True
    contents = None
    s3_client = get_client()
    result = s3_client.list_objects(Bucket=bucket, Prefix=key_name)

    if result:
        contents = result.get('Contents', None)
        if contents:
            for content in contents:
                if content.get('Key') != key_name:
                    empty = False
                    break

    return (empty, contents)


def check_key(key_name, bucket=BUCKET_DEFAULT):
    """
    Check if a S3 key exists
    """
    key = get_key(key_name, bucket)
    return key is not None


def check_prefix(prefix, bucket=BUCKET_DEFAULT):
    """
    Check if a S3 prefix exists
    """
    s3_client = get_client()
    results = s3_client.list_objects(Bucket=bucket, Prefix=prefix)
    return 'Contents' in results


def check_size(key, bucket=BUCKET_DEFAULT):
    """
    Check the size of a s3 file (key) in a bucket
    """
    s3_client = get_client()
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        size = response['ContentLength']
        return size > 0
    except Exception as ex:
        LOGGER.debug(ex)
        pass
    return False


def check_unequal_files(first_file, second_file):
    """
    Checks if S3 file objects returned from get_key are unequal sizes in bytes.
    :param first_file: First S3 file object.
    :param second_file: Second S3 file object.
    :return: Boolean, True if files are different sizes, False if files are the same size.
    """
    return first_file.size != second_file.size


def clean_json(contents):
    """
    Clean out trailing commas in JSON string contents
    """
    import re
    contents = re.sub(",[ \t\r\n]*}", " }", contents)
    contents = re.sub(",[ \t\r\n]*]", " ]", contents)
    return contents


def convert_parquet_to_json(parquet_content):
    """
    Convert parquet content to json object
    """
    data = []
    for parquet in parquet_content.strip().split("\n"):
        LOGGER.debug("- Parquet: %s\n", parquet)
        # parquet = clean_json(parquet)  # removing trailing commas
        data.append(json.loads(parquet))
    return data


def copy_contents_to_bucket(contents, key_name, bucket=BUCKET_DEFAULT):
    """
    Copy a string content to specified key in s3 bucket and
    overwrite original key if it already exists
    """
    s3_client = get_client()
    key = get_key(key_name, bucket)
    msg = "{} [{}]".format(key_name, bucket)
    if key is None:
        LOGGER.debug('new key: %s', msg)
    else:
        LOGGER.debug('deleting %s', msg)
        # acl = s3_client.get_object_acl(Bucket=bucket, Key=key_name)
        s3_client.delete_object(Bucket=bucket, Key=key_name)
    LOGGER.debug('put_object: %s', msg)
    try:
        return s3_client.put_object(Body=contents, Bucket=bucket, Key=key_name)
    except Exception as ex:
        LOGGER.error('failure on putting %s:\n%s', msg, ex)
    return None


def copy_to_bucket(filename, prefix_path=PREFIX_MINED, bucket=BUCKET_DEFAULT):
    """
    Upload a local file per path prefix in bucket

    @param filename: the full path to local filename
    @param prefix: the prefix (starting under the bucket) of the key name
    @param bucket: the bucket name (top-level directory in S3)

    @return: True if upload succeeded; otherwise, False

    example:
        copy_to_bucket("/Users/overload/test.json", "mined-json")
    """
    import os
    try:
        s3_resource = get_resource()
        if os.path.isfile(filename):
            basename = os.path.basename(filename)
            prefix = prefix_path.strip('/') + "/" + basename
            LOGGER.debug("uploading [" + filename + "] to [" + prefix + "]")
            s3_resource.meta.client.upload_file(filename, bucket, prefix)
            LOGGER.debug("uploaded: [" + prefix + "]")
        else:
            LOGGER.error("cannot find: %s", filename)
            return False
    except Exception as ex:
        LOGGER.error(ex)
        return False
    return True


def create_key(contents, key_name, bucket=BUCKET_DEFAULT):
    """Create a key on s3"""
    try:
        s3_client = get_client()
        return s3_client.put_object(Body=contents, Bucket=bucket, Key=key_name)
    except Exception as ex:
        LOGGER.error('failure on creating %s [%s]:\n%s', key_name, bucket, ex)
        return None


def delete_empty_folder(key_name, bucket=BUCKET_DEFAULT):
    """
    delete an S3 folder (key suffix '/') if it is empty
    """
    if not str(key_name).endswith('/'):
        return False

    empty = True
    contents = None
    s3_client = get_client()
    result = s3_client.list_objects(Bucket=bucket, Prefix=key_name)

    if result:
        contents = result.get('Contents', None)
        if contents:
            for obj in contents:
                if obj.get('Key', '') != key_name:
                    empty = False
                    break
    if contents and empty:
        LOGGER.info("empty folder: %s [bucket=%s]", key_name, bucket)
        return delete_key(key_name, bucket)
    return False


def delete_key(key_name, bucket=BUCKET_DEFAULT):
    """
    Deleting a s3 bucket key

    Dev-note: comparing to using boto3.resource('s3')
        s3 = get_resource()
        s3.Object(bucket, key_name).delete()
    """
    try:
        s3_client = get_client()
        LOGGER.info("deleting key: %s [bucket=%s]", key_name, bucket)
        s3_client.delete_object(Bucket=bucket, Key=key_name)
        return True
    except Exception as ex:
        LOGGER.debug(ex)
        return False


def get_client():
    """
    Get S3 client
    note: This function can be customized to accept configurations
    """
    session = boto3_session.Session()
    s3_client = session.client('s3', config=CONFIG)
    return s3_client


def get_csv_data(key_name, bucket):
    """
    Get csv data from S3.
    Data will be parsed to a string.
    @param key_name: path of csv file
    @param bucket: bucket name
    @return: <str> string representing the csv content
    """
    csv_content_str = get_content(key_name, bucket).decode('utf-8')
    csv_content_str = csv_content_str.replace('\r\n', '\n')
    csv_content_str = csv_content_str.strip().strip('\n').strip('\ufeff')
    return csv_content_str


def get_resource():
    """
    Get S3 resource
    note: This function can be customized to accept configurations
    """
    session = boto3_session.Session()
    s3_resource = session.resource('s3', config=CONFIG)
    return s3_resource


def get_content(key_name, bucket=BUCKET_DEFAULT):
    """
    Get content from a s3 file (key_name) in a bucket
    """
    s3_client = get_client()
    try:
        LOGGER.debug("- getting object: %s [bucket='%s']", key_name, bucket)
        response = s3_client.get_object(Bucket=bucket, Key=key_name)
        size = response['ContentLength']
        if size > 0:
            LOGGER.debug("- reading object: %s [size=%s]", key_name, size)
            contents = response['Body'].read()  # .decode('utf-8')
            return contents
        else:
            LOGGER.debug("- content zero: %s", key_name)
            return ""
    except Exception as ex:
        LOGGER.debug("- content error: %s", key_name)
        LOGGER.debug(ex)

    return None


def get_file_contents_s3(bucket_name, key):
    """
    Retrieves file contents for a file on S3 and streams it over.
    :param bucket_name: bucket to get contents from
    :param key: path to the file
    :return: the contents of the file if they exist otherwise none
    """
    s3_client = boto3.resource('s3').Object(bucket_name, key)

    try:
        file_contents = s3_client.get()['Body'].read()
    except ClientError:
        file_contents = None
        LOGGER.info(FILE_NOT_FOUND_ERROR_MESSAGE)
    return file_contents


def get_json_data(key_name, bucket=BUCKET_DEFAULT):
    """
    Get JSON data obejct from a s3 file (key_name) in a bucket

    Note: using `json.loads()` to read from string,
          comparing to `json.load()` which read from local file directly
          ```
          with open('filename.json') as data_file:
              data = json.load(data_file)
          ```
    """
    json_content = get_content(key_name, bucket)
    if json_content:
        # logger.debug("- Data contents: %s\n", json_content)
        try:
            data = json.loads(json_content)
            LOGGER.debug("- JSON object: %s\n", json.dumps(data))
            return data
        except Exception as ex:
            LOGGER.debug(ex)

    return None


def get_json_files(prefix='', bucket=BUCKET_DEFAULT):
    """
    This function return a list of json files per prefix in bucket

    @param prefix: the prefix (starting under the bucket) of the key name
    @param bucket: the bucket name (top-level directory in S3)

    @return: a list of keys of *.json files

    example:
        get_json_files("mined-json/2017")
    """
    files = []

    # pylint: disable=unused-argument
    def get_func(key_name, **kwargs):
        """Append key name to file list"""
        files.append(key_name)

    process_json(get_func, prefix, bucket=bucket)
    return files


def get_key(key_name, bucket=BUCKET_DEFAULT):
    """
    Get key object in s3 bucket
    """
    s3_resource = get_resource()
    bucket = s3_resource.Bucket(bucket)
    objects = list(bucket.objects.filter(Prefix=key_name))
    if len(objects) > 0 and objects[0].key == key_name:
        return objects[0]
    return None


def get_keys(prefix='', suffix='/', **kwargs):
    """
    This function return a list of s3 keys per prefix and suffix in bucket

    @param prefix: the prefix (starting under the bucket) of the key name
    @param suffix: the suffix (ending) of the key name

    @return: a list of s3 keys

    example:
        get_keys("mined-json/2017", ".json")
    """
    keys = []

    # pylint: disable=unused-argument
    def get_func(key_name, **kwargs):
        """Append key to key list"""
        keys.append(key_name)

    process(get_func, prefix, suffix, **kwargs)
    return keys


def get_parquet_data(key_name, bucket=BUCKET_DEFAULT):
    """
    Get parquet data from a s3 file (key_name) in a bucket

    Note: For parquet contents, each line is in valid JSON format
          but the file itself is not.
    """
    parquet_content = get_content(key_name, bucket)
    if parquet_content:
        # logger.debug("- Data contents: %s\n", parquet_content)
        try:
            data = convert_parquet_to_json(parquet_content)
            LOGGER.debug("- JSON object: %s\n", json.dumps(data))
            return data
        except Exception as ex:
            LOGGER.debug(ex)
    return None


# pylint: disable=invalid-name
def mv(old_path, new_path, filename, s_bucket=BUCKET_DEFAULT):
    """
    Rename/move a file from old path to new path with specific s3 bucket

    @param old_path: the original path (prefix of the original key name)
    @param new_path: the new path (prefix of the destinated key name)
    @param filename: the file name (suffix following the path) of the key name
    @param s_bucket: the s3 bucket (top-level directory in S3)

    @return: True if the operation succeeded; otherwise, False
    """
    LOGGER.debug(
        "moving file: '" + filename + "' from [" +
        old_path + "] to [" + new_path + "]")
    oldkey = old_path + '/' + filename
    newkey = new_path + '/' + filename

    try:
        client = get_client()
        source = s_bucket + '/' + oldkey  # the source must include bucket name
        LOGGER.debug("moving [" + oldkey + "] to [" + newkey + "]")
        client.copy_object(Bucket=s_bucket, CopySource=source, Key=newkey)
        client.delete_object(Bucket=s_bucket, Key=oldkey)
    except Exception:
        return False

    return True


def mv_key(oldkey, newkey, bucket=BUCKET_DEFAULT):
    """
    Rename/move an old key to new key within specific s3 bucket

    @param oldkey: the original key name (file name)
    @param newkey: the new key name (file name)
    @param bucket: the bucket name (top-level directory in S3)

    @return: True if the operation succeeded; otherwise, False
    """
    try:
        s3_resource = get_resource()
        source = bucket + '/' + oldkey  # the source must include bucket name
        LOGGER.debug("moving [" + oldkey + "] to [" + newkey + "]")
        s3_resource.Object(bucket, newkey).copy_from(CopySource=source)
        s3_resource.Object(bucket, oldkey).delete()
        return True
    except Exception:
        return False


def process_func(key, **kwargs):
    """
    default function that can be passed to process()
    """
    import sys
    contents = "{} - {}\n".format(str(key), str(kwargs))
    sys.stdout.write(contents)


def process_json(a_func=process_func, prefix='', **kwargs):
    """
    Process all json files in the bucket with specified prefix
    """
    process(a_func, prefix, '.json', **kwargs)


def generate_pages(prefix='', **kwargs):
    """
    This function creates a paginator and yields one page at a time.

    :param prefix: the prefix (starting under the bucket) of the key name
    :return: one page of contents
    """
    bucket = kwargs.get('bucket', BUCKET_DEFAULT)
    max_items = kwargs.get('max_items', None)
    check_arg_bucket(bucket)

    s3_client = get_client()
    paginator = s3_client.get_paginator('list_objects')
    parameters = {'Bucket': bucket, 'Prefix': prefix, 'Delimiter': '', 'PaginationConfig':{'MaxItems': max_items}}
    p_iterator = paginator.paginate(**parameters)

    for obj in p_iterator.search('Contents'):
        if obj:
            key_name = obj.get('Key', '')
            if key_name.endswith("/"):
                LOGGER.info("- skipping key: %s", key_name)
                continue
            yield obj


# process calls a_func to process all keys in a bucket
def process_keys(a_func=process_func, prefix='', **kwargs):
    """
    This function calls specified a_func to process all keys with
    any specific prefix in a S3 bucket

    @param a_func: the process function to take each iterated key name
                   the function signature is `def func(obj, **kwargs)`
    @param prefix: the prefix (starting under the bucket) of the key name
    @param kwargs: the additional parameters for a_func
    @return: N/A

    example:
        process_keys(process_func, "hancock/mined-json", bucket="cyber-intel")
    """
    bucket = kwargs.get('bucket', BUCKET_DEFAULT)

    check_arg_as_func(a_func)
    check_arg_bucket(bucket)

    s3_client = get_client()

    paginator = s3_client.get_paginator('list_objects')
    parameters = {'Bucket': bucket, 'Prefix': prefix, 'Delimiter': ''}
    p_iterator = paginator.paginate(**parameters)
    counts = 0

    for obj in p_iterator.search('Contents'):
        if obj:
            key_name = obj.get('Key', '')
            if key_name.endswith("/"):
                LOGGER.info("- skipping key: %s", key_name)
                delete_empty_folder(key_name, bucket)
                continue
            a_func(obj, **kwargs)
            counts += 1

    return counts


# process calls a_func to process all keys by prefix and suffix in a bucket
def process(a_func=process_func, prefix='', suffix='/', **kwargs):
    """
    This function calls specified a_func to process
    any specific prefix with delimiter (suffix) in a S3 bucket

    @param a_func: the process function to take each iterated key name
                   the function signature is `def func(key_name, **kwargs)`
    @param prefix: the prefix (starting under the bucket) of the key name
    @param suffix: the suffix (ending) of the key name
    @param kwargs: the additional parameters for a_func
    @return: N/A

    example:
        process(process_func, "hancock/", ".json", bucket="cyber-intel")

    caution:
        the patterns of prefix and suffix match all keys in the bucket, e.g.
            prefix + '/20170116_test.' + suffix
            prefix + '/some/other/folder/foo.' + suffix
            prefix + suffix
        this requires extra step to parse the key name, in order to only
        process "files" directly existing under a prefix "dir/path/"
        since s3 has no hierarchical directory
    """
    bucket = kwargs.get('bucket', BUCKET_DEFAULT)

    if not kwargs.get('chck_bypass', False):
        check_arg_as_func(a_func)
        check_arg_bucket(bucket)

    s3_client = get_client()

    paginator = s3_client.get_paginator('list_objects')
    parameters = {'Bucket': bucket, 'Prefix': prefix, 'Delimiter': suffix}
    iterator = paginator.paginate(**parameters)
    counts = 0

    # logger.info("-- searching: %s", str(parameters))
    if suffix:
        for path in iterator.search('CommonPrefixes'):
            if path is not None:
                # logger.debug("-- path: %s", str(path))
                key = path.get('Prefix', None)
                if key:
                    a_func(key, **kwargs)
                    counts += 1
    else:
        for path in iterator.search('Contents'):
            if path is not None:
                # logger.debug("-- path: %s", str(path))
                key = path.get('Key', None)
                if key:
                    a_func(key, **kwargs)
                    counts += 1
    return counts


def validate_file_on_s3(bucket_name, key):
    """
    Checks if a file exists on S3 and non-zero size.
    :param bucket_name: Name of the bucket to check
    :param key: path to the file
    :return: true if file exists otherwise false
    """
    s3_client = boto3.resource('s3')

    file_obj = s3_client.Object(bucket_name, key)
    is_valid_file = True
    try:
        # Checks file size if it's zero
        if file_obj.get()['ContentLength'] == 0:
            is_valid_file = False
            LOGGER.info(FILE_SIZE_ZERO_ERROR_MESSAGE)
    except ClientError:
        # Means the file doesn't exist
        is_valid_file = False
        LOGGER.info(FILE_NOT_FOUND_ERROR_MESSAGE)

    return is_valid_file
