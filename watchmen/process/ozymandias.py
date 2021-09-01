"""
Created August 2021

This watchman is designed to check status of reflections pulled out on the fly by dremio.py based on information
specified in the config, dremoio_targets.yaml.
Currently the checks that can be performed are for reflections that already be created and that does not start
with tmp. Reflections status are checked every 60minutes


@author: Olawole Frankfurt Ogunfunminiyi
@email: oogunfunminiyi@infoblox.com
"""

import datetime
import os
import traceback
import yaml
import watchmen.utils.dremio as dremio
from watchmen import const, messages
from watchmen.common.result import Result
from watchmen.common.watchman import Watchman
from watchmen.config import settings

CONFIG_NAME = settings('ozymandias.targets')

SECRETE_PATH = settings('ozymandia.dremio_secret_path')
ROOT_URL = settings('ozymandia.ROOT_URL')
LOGIN_URL = settings('ozymandia.LOGIN_URL')
REFLECTION_URL = settings('ozymandia.REFLECTION_URL')
MESSAGES = messages.OZYMANDIAS
REGION = settings("ozymandia.targets.region")
secrete_name = settings("ozymandia.targets.secrete_name")
CONFIG_PATH = os.path.join(
    os.path.realpath(os.path.dirname(__file__)), 'configs', CONFIG_NAME)


class Ozymandias(Watchman):

    def __init__(self, event, context):
        """
        Ozymandias Constructor
        """
        super().__init__()
        self.event = event.get('Type')

    def monitor(self):
        """
        Monitors Dremio Targets in the config.yaml file
        :return: <List> A list of result objects from the checks performed on each target.
        """
        self.create_details()

    @staticmethod
    def create_details():
        """
        Creates details for the result objects from the new_change_strings and exception_strings if they exist.
        :param processed_target: <dict> A dictionary of the target name with any failures or exceptions that occurred
        :return: <str> A details string for the target with information from the checks performed
        Return list containing dictionary of reflection result
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
        secret = dremio.get_secret(SECRETE_PATH, REGION)
        token = secret[secrete_name]
        user_name = secret['username']
        auth_token = dremio.generate_auth_token(user_name, token, LOGIN_URL)
        reflection_list = dremio.get_reflection_list(auth_token, REFLECTION_URL)
        reflection_results = dremio.fetch_reflection_metadata(auth_token, REFLECTION_URL, reflection_list)
        computed_result = {}
        for reflection_result in reflection_results:
            reflectionid, name, failurecount = reflection_result["id"], reflection_result["name"], \
                                               reflection_result["status"]['failureCount']
            if failurecount == 3:
                computed_result[reflectionid]: {name: failurecount}
        final_result = Ozymandias.determine_result(computed_result, datetime.now())
        return final_result

    def determine_result(self, reflection_final_result, details=None) -> {}:
        """
        Determine the outcome of the check
        If {reflection_final_result} is not empty, Failed reflections present in {}
        Otherwise, if no exception, No reflection failled, outcome is success
        If connection to dremio or other errors? Exception is thrown.
        """
        if bool(reflection_final_result):
            disable_notifier = False
            short_message = MESSAGES.get("reflection_failled_message")
            state = Watchman.STATE.get("failure")
            subject = MESSAGES.get("failure_detected_subject")
            success = False

        elif Exception:

            disable_notifier = False
            short_message = MESSAGES.get("reflection_exception_message")
            state = Watchman.STATE.get("exception")
            subject = MESSAGES.get("reflection_exception_subject")
            success = False
        else:
            disable_notifier = True,
            short_message = MESSAGES.get("reflection_success_message")
            state = Watchman.STATE.get("success")
            subject = MESSAGES.get("reflection_success_subject")
            success = True

        return Result(
            details=details,
            disable_notifier=disable_notifier,
            short_message=short_message,
            snapshot={},
            watchman_name=self.watchman_name,
            state=state,
            subject=subject,
            success=success,
            target=REFLECTION_URL
        )
