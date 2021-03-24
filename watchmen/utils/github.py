"""
The Github Util contains functions to access the GitHub API
Note: A regular authenticated request (with a token):
        - Rate limit of 5000 per hour
        - Allows for fine grain control of util permissions
      An unauthenticated request (without a token):
        - Rate limit of 60 per hour
        - Good for local testing

@author Phillip Hecksel
@email phecksel@infoblox.com
"""

import requests
import traceback

from logging import getLogger
from watchmen import const

LOGGER = getLogger(__name__)
API_URL = 'https://api.github.com'

