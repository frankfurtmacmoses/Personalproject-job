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


def _check_endpoint(config, **kwargs):
    env = config.get('env')   # I dont know why this important
    status_code = config.get('status', 200)

    parent = {}
    parent.update(kwargs)

    base_url = parent.get('path', '')
    path = config.get('path')
    if parent:
        parent_path = parent.get(kwargs.keys()[0]).get('path')
    else:
        parent_path = parent.get('path')

    if parent_path is not None:
        path = "{}{}".format(parent_path, path)

    format = config.get('format', 'json')

    data = requests.get(path)

    # Checking status, json, and keys
    if not data.status_code == status_code:
        print ("Different status code!")
        return
    # if it is the parent, then there should be no JSON file to check
    # so this says check if it's the parent and loads JSON data
    try:
        data.json()
    except Exception as ex:
        if parent_path is not None:
            print("Not a JSON file!")
        else:
            return






# pylint: disable=unused-argument
def main(event, context):
    """
    main function
    :return: status of Sockeye endpoints
    """
    with open("endpoints.json") as data_file:
        data = json.load(data_file)[0]   # converting list to dict

    _check_endpoint(data)
    routes = data.get('routes')
    if not isinstance(routes, list):
        return
    for route in routes:
        _check_endpoint(route, data=data)

if __name__ == '__main__':
    main(None, None)
