"""
Created May 2021

This watchman is designed to check for updates to Github Repos specified in the config, github_targets.yaml.
Currently the checks that can be performed are for new commits and new releases. This watchman makes use of the Github
util to check on repos and is limited to 5000 requests per hour for authenticated users (user token is passed)
and 60 requests per hour for unauthenticated users (no user token is passed). A failure represents an update, or change
to a repo. An exception represents an error that occurred in the code, or that occurred during a Github checks.

@author: Phillip Hecksel
@email: phecksel@infoblox.com
"""

from watchmen import const, messages
from watchmen.common.result import Result
from watchmen.common.watchman import Watchman
from watchmen.config import settings

DAILY = "Daily"
MESSAGES = messages.NITEOWL
TARGET_ACCOUNT = settings("TARGET_ACCOUNT", "atg")

EVENT_OFFSET_PAIR = {DAILY: 'days'}
GENERIC_TARGET = 'Generic Github {}'.format(TARGET_ACCOUNT)


class Niteowl(Watchman):

    def __init__(self, event, context):
        """
        Niteowl Constructor
        """
        super().__init__()
        self.event = event.get('Type')

    def monitor(self):
        """
        Monitors Github Targets in the github_targets.yaml file
        :return: <List> A list of result objects from the checks performed on each target.
        """

        if not self._is_valid_event():
            return self._create_invalid_event_result()

    def _create_invalid_event_result(self):
        """
        Creates a result object for if the event type is invalid
        :return: <list> A Result object for an invalid event type
        """
        return [Result(
            details=MESSAGES.get("exception_invalid_event_details"),
            disable_notifier=False,
            short_message=MESSAGES.get("exception_message"),
            snapshot={},
            state=Watchman.STATE.get("exception"),
            subject=MESSAGES.get("exception_invalid_event_subject"),
            success=False,
            target=GENERIC_TARGET,
            watchman_name=self.watchman_name,
        )]

    def _is_valid_event(self):
        """
        A check to make sure the event is supported by niteowl
        :return: if the event is in the list of time offsets used for performing github checks
        """
        return self.event in list(EVENT_OFFSET_PAIR.keys())

