"""
Created on July 17, 2018

This module is meant to be used as a helper for other
Watchmen scripts. Most of this class can be utilized
for verifying simple checks in S3.

@author Daryan Hanshew
@email dhanshew@infoblox.com

"""
# Python imports
from datetime import datetime, timedelta
from logging import getLogger, basicConfig, INFO
import pytz
# External Libraries
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

LOGGER = getLogger("Universal Watchmen")

FILE_NOT_FOUND_ERROR_MESSAGE = "FILE DOESN'T EXIST!"
FILE_SIZE_ZERO_ERROR_MESSAGE = "FILE SIZE IS ZERO!"
EMPTY_METRIC_ERROR = "No metric found for: "


class Watchmen(object):
    """
    universal watchmen class
    """
    def __init__(self, bucket_name=''):
        basicConfig(level=INFO)
        self.s3_client = boto3.resource('s3')
        self.dynamo_client = boto3.resource('dynamodb')
        self.bucket_name = bucket_name

    def validate_file_on_s3(self, key):
        """
        Checks if a file exists on S3 and non-zero size.
        :param key: path to the file
        :return: true if file exists otherwise false
        """
        file_obj = self.s3_client.Object(self.bucket_name, key)
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

    def get_file_contents_s3(self, key):
        """
        Retrieves file contents for a file on S3 and streams it over.
        :param key: path to the file
        :return: the contents of the file if they exist otherwise none
        """
        try:
            file_contents = self.s3_client.Object(self.bucket_name, key).get()['Body'].read()
        except ClientError:
            file_contents = None
            LOGGER.info(FILE_NOT_FOUND_ERROR_MESSAGE)
        return file_contents

    def get_hourly_feed_metrics(self, table_name, feed):
        """
        Retrieves metrics for a particular feed.
        :param table_name: name of table being searched
        :param feed: feed itself being checked
        :return: metrics for a particular feed
        """
        check_time = (datetime.now(pytz.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H").replace('/', '')
        metric = {}
        table = self.dynamo_client.Table(table_name)
        response = table.query(
            KeyConditionExpression=Key('timestamp').eq(check_time)
        )
        for item in response.get('Items'):
            if item.get('source') == feed:
                metric = item.get('metric')
                break

        if not metric:
            LOGGER.info(EMPTY_METRIC_ERROR + feed)
        return metric

    @staticmethod
    def check_feed_metric(metric, minimum, maximum):
        """
        Compares feed metric along two values.
        :param metric: the metric to be compared
        :param minimum: max amount metric should be
        :param maximum: min amount metric should be
        :return: if the metric is in range
        """
        return minimum < metric < maximum
