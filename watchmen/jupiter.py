"""
Created on January 29, 2019

This script monitors Sockeye ensuring the database and endpoints are working correctly for all endpoints on Sockeye.
If data is not found in the database or the endpoint does work correctly, an SNS will be sent.

@author: Kayla Ramos
@email: kramos@infoblox.com
"""
from logging import getLogger, basicConfig, INFO
from utils.sns_alerts import raise_alarm
from utils.universal_watchmen import Watchmen
import requests, json

LOGGER = getLogger("Jupiter")
basicConfig(level=INFO)

# Message constants
NO_ROUTES = "There are no routes to be checked! Check endpoints.json!"
NO_ROUTES_MESSAGE = "Base page does not have any routes to check. Please check endpoints.json or contact "

# pylint: disable=unused-argument
def main(event, context):
    """
    main function
    :return: status of Sockeye endpoints
    """

    with open("endpoints.json") as data_file:
        points = json.load(data_file)



if __name__ == '__main__':
    main(None, None)
