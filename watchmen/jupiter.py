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
import pytz, requests, json


LOGGER = getLogger("Jupiter")
basicConfig(level=INFO)

# Filepath Strings
BUCKET_NAME = "cyber-intel"
URL_PREFIX = "http://sng.r11.com/v1/"


def queryJSON(data):
    data = json.loads(json.dumps(data))


def checkEndpoints(endpoints):
    # Loop through and see if endpoints return 200
    for point in endpoints:
        try:
            r = requests.get('{}{}'.format(URL_PREFIX, point))
        except requests.exceptions.ConnectionError:
            r.status_code = "Connection refused"
        data = r.json()
        queryJSON(data)


# pylint: disable=unused-argument
def main(event, context):
    """
    main function
    :return: status of the file
    """
    #watcher = Watchmen(bucket_name=BUCKET_NAME)

    #for now, hard-coded list of endpoints
    # once I make the s3 file that contains all the end-points, I will validate and then get contents
    # if that doesn't work, then I use local copy of endpoint.json containing all the endpoints
    # local endpoint.json may not be update
    endpoints = ["info", "data/info", "hancock/info", "truth/info"]
    checkEndpoints(endpoints)




if __name__ == '__main__':
    main(None, None)
