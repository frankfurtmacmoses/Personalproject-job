"""
Created on June 19, 2018

AWS to raise SNS alerts for watchmen alerts

@author: Daryan Hanshew
@email: dhanshew@infoblox.com
"""
# External libraries
import boto3
from logging import getLogger

LOGGER = getLogger(__name__)


def get_sns_client():
    """
    Retrieves SNS client.
    :return: The SNS client
    """
    session = boto3.Session()
    sns_client = session.client('sns')
    return sns_client


def raise_alarm(topic_arn, msg, subject):
    """
    raise alarm
    """
    print("***Sounding the Alarm!***\n" + msg)
    sns_client = get_sns_client()
    response = sns_client.publish(
        TopicArn=topic_arn,
        Message=msg,
        Subject=subject
    )
    try:
        assert response['ResponseMetadata']['HTTPStatusCode'] == 200, \
            "ERROR Publishing to sns failed!"
    except KeyError:
        LOGGER.error("Error: Response did not contain HTTPStatusCode\n")
        LOGGER.error(response)
