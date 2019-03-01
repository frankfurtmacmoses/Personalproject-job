"""
# common/api.py - generic urllib wrapper

# author: jason_zhuyx@hotmail.com (dockerian/pyml)
# date: 2019-01-28
"""
import json
import httplib
import logging
import requests
import traceback

from watchmen.config import get_uint, settings
from watchmen.utils.logger import get_logger

# pylint: disable=no-member
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
DEBUG_LEVEL = DEBUG_LEVEL = get_uint('debug.level', logging.INFO)
LOGGER = get_logger(__name__, level=DEBUG_LEVEL)


def get_api_data(api_url, api_headers={}, api_data=None, timeout=20):
    """
    @param api_url: a string represent full api URL.
    @param api_headers: a directory of request headers.
    @param api_data: a JSON data for POST request.
    @param timeout: max amount of time a request will attempt to connect
    @return: (<api data object>, <status>).
    """
    _status = None
    api_obj = None

    if not isinstance(timeout, tuple) and not isinstance(timeout, int):
        timeout = settings('api.timeout', 20)
    try:
        res = requests.get(
            api_url, headers=api_headers, data=api_data, verify=False, timeout=timeout)
        _status = res.status_code if hasattr(res, 'status_code') else None
        if res and _status == 200:
            data = res.text
            # LOGGER.debug('- response:\n%s', res.info())
            headers = res.headers
            content_type = headers.get('content-type', '').split(';')[0]
            decoded_data = data.decode('utf-8', errors='ignore')
            LOGGER.info('- decoded data: %s', decoded_data)
            if 'application/json' in content_type:
                api_obj = json.loads(decoded_data)
            else:
                api_obj = {'data': decoded_data}
        elif not res:
            LOGGER.error('- unable to open api request: {}'.format(api_url))
        else:
            LOGGER.debug('- response:\n%s', res.info())
            LOGGER.error('- status: %s, request: %s', _status, api_url)
    except requests.Timeout as ex:
        message = 'unable to complete request within allotted timeout period'
        LOGGER.error('- %s: %s', message, api_url)
        _status = httplib.REQUEST_TIMEOUT
    except Exception:
        message = 'unable to read data from request'
        LOGGER.error('- %s: %s', message, api_url)
        # import sys
        # exc_info = '{}: {}'.format(type(ex).__name__, ex)
        # exc_type, exc_obj, exc_tb = sys.exc_info()
        # traceback.print_stack()
        traceback.print_exc()

    return api_obj, _status
