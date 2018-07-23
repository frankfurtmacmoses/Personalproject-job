"""
Created on July 17, 2018

This module is meant to be used as a helper for other
Watchmen scripts. Most of this class can be utilized
for verifying simple checks in S3.

@author Daryan Hanshew
@email dhanshew@infoblox.com

"""
# Python imports
from logging import getLogger
# External Libraries
import boto3
from botocore.exceptions import ClientError

LOGGER = getLogger(__name__)

FILE_NOT_FOUND_ERROR_MESSAGE = "FILE DOESN'T EXIST!"
FILE_SIZE_ZERO_ERROR_MESSAGE = "FILE SIZE IS ZERO!"


class Watchmen(object):
    """
    universal watchmen class
    """
    def __init__(self):
        self.s3_client = boto3.resource('s3')

    def validate_file_on_s3(self, bucket_name, key):
        """
        Checks if a file exists on S3 and non-zero size.
        :param bucket_name: name of bucket
        :param key: path to the file
        :return: true if file exists otherwise false
        """
        file_obj = self.s3_client.Object(bucket_name, key)
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

    def get_file_contents_s3(self, bucket_name, key):
        """
        Retrieves file contents for a file on S3 and streams it over.
        :param bucket_name: name of bucket
        :param key: path to the file
        :return: the contents of the file if they exist otherwise none
        """
        try:
            file_contents = self.s3_client.Object(bucket_name, key).get()['Body'].read()
        except ClientError:
            file_contents = None
            LOGGER.info(FILE_NOT_FOUND_ERROR_MESSAGE)
        return file_contents
