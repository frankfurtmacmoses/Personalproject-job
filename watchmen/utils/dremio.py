"""
The Dremio Util contains functions to access the Dremio API
Note: A regular authenticated request (with a token):
        - Rate limit of 5000 per hour
        - Allows for fine grain control of util permissions
      An unauthenticated request (without a token):
        - Rate limit of 60 per hour
        - Good for local testing

@author Olawole Frankfurt Ogunfunminiyi
@email oogunfunminiyi@infoblox.com
"""


import requests
import traceback
import logging
import json
from watchmen import const

dremioServer = 'dremio-dev.test.infoblox.com:9047'
dremio_sql_url = f"https://{dremioServer}/api/v3/sql"
dremio_job_url = f"https://{dremioServer}/api/v3/job"
reflection_url = f"https://{dremioServer}/api/v3/reflection"
dremio_login_url = f"https://{dremioServer}/apiv2/login"


def fetch_reflection_metadata(token, reflection_list, reflection_url):
    """     Send get request to reflection  by id in a loop
            and append the result to a list
            id: key value for the reflection asset
            token: Auth token for Dremio
            reflection_url: URL string with tokens to reflection
            """
    reflections_status = []
    for reflection in reflection_list:
        reflection_id = reflection[id]
        logging.info(reflection_url / {reflection_id})
        headers = {
            'Authorization': token,
            'Content-Type': "application/json",
            'cache-control': "no-cache"
        }
        response = requests.get(reflection_url / f'{reflection_id}', headers=headers)
        logging.info(f"Response from Dremio reflection metadata{str(response)}")
        result = pull_reflection_status(response)
        reflections_status.append(result)
        """
        Dictionary of : 
        """
        return reflections_status


def get_reflection_list(token, reflection_url):
    """     Send get request to reflection   asset by id
        id: key value for the reflection asset
        token: Auth token for Dremio
        reflection_url: URL string with tokens to reflection

        """
    logging.info(reflection_url)
    headers = {
        'Authorization': token,
        'Content-Type': "application/json",
        'cache-control': "no-cache"
    }
    response = requests.get(reflection_url, headers=headers)
    logging.info(f"Response from Dremio reflection metadata{str(response)}")
    reflection_list = pull_reflection_basic_info(response)
    return reflection_list


def pull_reflection_basic_info(response):
    """
    Take json response from get_reflection_list containing all reflections
    and pull out just the name and the id(s)
    called by get_reflectionlist(response)
    """
    reflection_info = []
    elements = json.loads(response)
    for element in elements['data']:
        reflection_id, reflection_name = element['id'], element['name']
        reflection_info.append(reflection_id, reflection_name)
        """
        return list of reflections with id and name
        """
        return reflection_info


def pull_reflection_status(response):
    """
     Get information about single reflection and return ->  "status": {
        "config": "OK",
        "refresh": "SCHEDULED",
        "availability": "AVAILABLE",
        "combinedStatus": "CAN_ACCELERATE",
        "failureCount": 0,
        "lastDataFetch": "2021-08-16T20:55:58.311Z",
        "expiresAt": "2021-08-16T23:55:58.311Z"
      }
    """
    elements = json.loads(response)
    status = elements['data']['status']
    return status
