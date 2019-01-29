"""
Created on January 29, 2019

This script monitors Sockeye ensuring the database and endpoints are working correctly for all endpoints on Sockeye.
If data is not found in the database or the endpoint does work correctly, an SNS will be sent.

@author: Kayla Ramos
@email: kramos@infoblox.com
"""
from datetime import datetime, timedelta
from logging import getLogger, basicConfig, INFO
from utils.sns_alerts import raise_alarm
from utils.universal_watchmen import Watchmen
import pytz, requests, json, sys


LOGGER = getLogger("Jupiter")
basicConfig(level=INFO)

# File Strings
BUCKET_NAME = "cyber-intel"
URL_PREFIX = "http://sng.r11.com/v1/"
USER = "cyberint_dev"

# Message Strings
EMPTY_DB_ERROR = " does not have any data in database!"
ENDPOINT_ERROR = "There is not a JSON file on "
SUCCESS_MESSAGE = "All sockeye endpoints have DB info and correct users!"


def queryJSON(point, data):
    """
    Check DB for data, and if the JSON file has a currentUser key, make sure it is the expected user
    :param data: JSON data pulled from endpoint
    :return: status message (nothing if everything is working)
    """
    message = ''
    try:
        data = json.loads(json.dumps(data))
        if not (data["dbInfo"]["dbSizeInMb"] > 0):
            LOGGER.info('{}{}'.format(point, EMPTY_DB_ERROR))
            message = 'Endpoint \'{}\'{}'.format(point, EMPTY_DB_ERROR)
        try:
            data["dbInfo"]["currentUser"]
            if not (data["dbInfo"]["currentUser"] == USER):
                print("The user is incorrect!")
        except KeyError:
            pass
    except Exception as ex:
        print("Something broke")

    return message


def checkEndpoint(point):
    """
    Checks if endpoints are accessible
    :param point: endpoint that is being checked
    :return: JSON file contents
    """
    try:
        r = requests.get('{}{}'.format(URL_PREFIX, point))
        data =r.json()
    except Exception as ex:
        LOGGER.error(ex)
        LOGGER.info('{}{}{}, Please check URL prefix'.format(ENDPOINT_ERROR, URL_PREFIX, point))
        raise Exception('{}{} does not have an accessible JSON file'.format(URL_PREFIX, point))
    return data


# pylint: disable=unused-argument
def main(event, context):
    """
    main function
    :return: status of Sockeye endpoints
    """
    #watcher = Watchmen(bucket_name=BUCKET_NAME)

    #for now, hard-coded list of endpoints
    # once I make the s3 file that contains all the end-points, I will validate and then get contents
    # if that doesn't work, then I use local copy of endpoint.json containing all the endpoints
    # local endpoint.json may not be update
    message = ''
    endpoints = ["info", "data/info", "hancock/info", "truth/info"]
    for point in endpoints:
        message += queryJSON(point, checkEndpoint(point)) + '\n'

    if message.isspace():
        print(SUCCESS_MESSAGE)
        #return SUCCESS_MESSAGE
    else:
        print(message)
        #return message




if __name__ == '__main__':
    main(None, None)
