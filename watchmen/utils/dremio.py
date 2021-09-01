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
import logging
import boto3
import boto3.session
import json
import base64
from botocore.exceptions import ClientError
import requests
import traceback
import logging
import json


def fetch_reflection_metadata(token, reflection_url, reflection_list):
    """     Send get request to reflection  by id in a loop
            and append the result to a list
            id: key value for the reflection asset
            token: Auth token for Dremio
            reflection_url: URL string with tokens to reflection
            """
    reflections_status = []
    for reflection in reflection_list:
        reflection_id = reflection_list.get(reflection)

        logging.info(reflection_url + reflection_id)
        headers = {
            'Authorization': token,
            'Content-Type': "application/json",
            'cache-control': "no-cache"
        }
        try:
            response = requests.get(f"{reflection_url}"+reflection_id, headers=headers)
        except requests.exceptions.RequestException as e:
            logging.error(f"Response from Dremio reflection metadata{str(response)}")
            raise SystemExit(e)
        result = _pull_reflection_status(response.json())
        reflections_status.append(result)
        print(reflections_status)


def _pull_reflection_status(response):
    """
    "id":
     Get information about single reflection and return ->
     "id": ,
     "name":
     "status": {
        "config": "OK",
        "refresh": "SCHEDULED",
        "availability": "AVAILABLE",
        "combinedStatus": "CAN_ACCELERATE",
        "failureCount": 0,
        "lastDataFetch": "2021-08-16T20:55:58.311Z",
        "expiresAt": "2021-08-16T23:55:58.311Z"
      }
    """
    elements = response
    result = {"id": elements["id"], "name": elements["name"], "status": (elements["status"])}
    return result


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
    reflection_list = _pull_reflection_basic_info(response.json())
    return reflection_list


def _pull_reflection_basic_info(json_response):
    """
    Take json response from get_reflection_list containing all reflections
    and pull out just the name and the id(s)
    called by get_reflectionlist(response)
    """
    reflection_info = {}
    elements = json_response
    for element in elements['data']:
        reflection_id, reflection_name = (element['id'], element['name'])
        if not (str(reflection_name)).startswith('tmp'):
            ## Create a dictionary
            reflection_info[reflection_name] = reflection_id
    return reflection_info


def get_secret(secret_name, region_name):
    ## Get secret name and region in config  from Ozymandias Class
    secret = None
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        error_message = "Problems getting secret {secret_name} in {region_name} with exception {e}".format(
            secret_name=secret_name,
            region_name=region_name, e=e.response['Error']['Code'])
        logging.error(error_message)
        raise Exception(error_message)

    # Decrypts secret using the associated KMS CMK.
    # Depending on whether the secret is a string or binary, one of these fields will be populated.
    if 'SecretString' in get_secret_value_response:
        secret = json.loads(get_secret_value_response['SecretString'])
    else:
        secret = json.loads(base64.b64decode(get_secret_value_response['SecretBinary']))
    return secret


def generate_auth_token(user_name, secret_value, dremio_login_url):
    """
        Generates the auth token for communication with Dremio

         return '_dremiohliaml16hn9m99qpi1d6ungcs'
            """
    headers = {
        'Content-Type': "application/json",
        'cache-control': "no-cache"
    }
    try:
        response = requests.post(dremio_login_url,
                                 json={"userName": user_name,
                                       "password": secret_value},
                                 headers=headers)
    except requests.exceptions.RequestException as e:
        print(e.request)
    logging.info(f" Response from Dremio Generate Token {str(response)}")

    if 'token' not in response.json():
        return None

    # Grab authorization token from response
    # Grab authorization token from response
    return "_dremio" + response.json()['token']


def main():
    dremioServer = "dremio-dev.test.infoblox.com:9047"
    dremio_reflection_url = f"https://{dremioServer}/api/v3/reflection/"
    dremio_login_url = f"https://{dremioServer}/apiv2/login"
    reflection_list = []
    secret = get_secret(
        "arn:aws:secretsmanager:us-east-1:902917483333:secret:pat-dremio_dev_admin-reflection_refresh-UjWnqc",
        "us-east-1")
    token = secret['temp-pat-dremio_dev_admin-reflection_refresh']
    user_name = secret['username']
    auth_token = generate_auth_token(user_name, token, dremio_login_url)
    reflection_list = get_reflection_list(auth_token, dremio_reflection_url)
    fetch_reflection_metadata(auth_token, dremio_reflection_url, reflection_list)


if __name__ == '__main__':
    main()
