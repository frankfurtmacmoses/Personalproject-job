'''
Common library for utility functions

authors: lpeaslee, vcollooru
'''

import logging
import boto3
import boto3.session
import json
import base64
from botocore.exceptions import ClientError

def get_secret(secret_name, region_name):
    '''
    Given the secret name and the region of the Secret manager, this function will fetch the secret values
    '''
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
