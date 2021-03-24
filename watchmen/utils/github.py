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


def get_repository_commits(owner, repo, since=None, token=None, path=None):
    """
    Retrieves all new commits for the repo or a specified path from the 'since' date if there is one. If there is not a
    since date it will return all commits.
    :param owner: <str> The repo owner
    :param repo: <str> The github repository
    :param since: <datetime> A datetime object to mark the date to start checking for new commits
    :param path: <str> A path in the repo to retrieve commits for
    :param token: <str> The github account token
    :return: <list<dict>>, <str> A list of commits with its metadata, and a traceback
    """
    header = {}
    parameters = {}

    if token:
        header.update({'Authorization': f'token {token}'})
    if since:
        parameters.update({'since': since.isoformat()})
    if path:
        parameters.update({'path': path})

    try:
        response = requests.get(url=f'{API_URL}/repos/{owner}/{repo}/commits',
                                headers=header,
                                params=parameters)

        response.raise_for_status()

        return response.json(), None
    except Exception as ex:
        LOGGER.error("ERROR Retrieving Repo Commits!")
        LOGGER.info(const.MESSAGE_SEPARATOR)
        LOGGER.exception('{}: {}'.format(type(ex).__name__, ex))
        tb = traceback.format_exc()
        return None, tb

